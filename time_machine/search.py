#import os
#import re
import json
import requests
#import wayback
import pandas as pd
#from bs4 import BeautifulSoup
from retrying import retry
#from tqdm import tqdm
#from joblib import Parallel, delayed
from datetime import datetime, date, timedelta
from dateutil import parser
from dateutil.relativedelta import relativedelta

class Archive():
	def __init__(self, archive='ia'):
		if archive == 'ia':
			self.name = 'Internet Archive'
			self.cdx_server = 'http://web.archive.org/cdx/search/cdx'
			self.archive_root = 'https://web.archive.org/web/'
			self.timestamp_suffix='id_'
			pass
		else:
			print('This archive is curently not implemented')
		
		self.params = {
		    'output': 'json',
		    'limit' :'100000',
		    'showResumeKey': 'true'
		}

	'''call() is a helper function to deal with results exceeding the limit. 
	Do not call this function. Use get_all() instead.'''
	@retry(wait_random_min=1000, wait_random_max=2000, stop_max_attempt_number=3)
	def call(self):
		s = requests.Session()
		req = requests.Request(method='GET', url=self.cdx_server, params=self.params)
		prep = req.prepare()
		
		#print(prep.url)
		r = s.send(prep)
		data = json.loads(r.text)
		return data

	'''get() returns a list of all available archive snapshots for the queried url.'''
	def get(self, url, pattern, time_slots, diversify_all, diversify_intervals, results_per_interval, filter_errors, filter_redirects, filter_revisits):
		self.params['url'] = url
		more = True
		data = []
		columns = []


		print('Retrieving archived snapshots from ' + self.name + ' for ' + url + ' ', end='')

		while more:
			print('.', end='')
			tmp = self.call()
			columns = tmp[0]
			tmp.pop(0)
			if len(tmp) > int(self.params['limit']):
				self.params['resumeKey'] = tmp[-1][0]
				tmp.pop(-1)
				tmp.pop(-1)
			else:
				more = False  
			data = data + tmp
		data = pd.DataFrame(data, columns=columns) 

		print()
		print('Postprocessing results.')

		if filter_errors:
			data = data[~data['statuscode'].str.startswith('4')]
			data = data[~data['statuscode'].str.startswith('5')]
			
		if filter_redirects:
			data = data[~data['statuscode'].str.startswith('3')]
			
		if filter_revisits:
			data = data[data['statuscode'] != '-']
		
		if pattern:
			data = data[data['original'].str.contains(pattern)]

		if time_slots == 'all':
			pass

		else:
			tmp_data = pd.DataFrame()
			if diversify_all and url.endswith('*'):
				data = data.drop_duplicates('urlkey')
			data['timestamp'] = data['timestamp'].astype(int)
			data['interval'] = pd.cut(data.timestamp, time_slots)
			for group in data.groupby('interval'):
				tmp = group[1]
				if diversify_intervals and url.endswith('*'):
					tmp = tmp.drop_duplicates('urlkey')
				if len(tmp) > results_per_interval:
					tmp = tmp.sample(results_per_interval)
				tmp_data = tmp_data.append(tmp)
			data = tmp_data

		return data

	def check_incomplete():
		pass

	def query(self, query_url, include_subpages=False, include_subdomains=False, interval='all', results_per_interval=1, pattern=None, diversify_all=False, diversify_intervals=False ,start_date=None, end_date=None, filter_errors=True, filter_redirects=True, filter_revisits=True):

		if include_subpages:
			if not query_url.endswith('*'):
				query_url = query_url + '*'
		else:	
			if query_url.endswith('*'):
				query_url = query_url[:-1]
		
		if include_subdomains:
			if query_url.startswith('www.'):
				query_url = '*' + query_url[4:]
		else:
			if query_url.startswith('*'):
				query_url = query_url[1:]
		
		if start_date:
			start_date = parser.parse(start_date)
		else:
			start_date = parser.parse('2006-01-01')
		if end_date:
			end_date = parser.parse(end_date)
		else:
			end_date = datetime.now()

		if start_date > end_date:
			print('Start date needs to be before end date.')
			return

		if interval == 'all':
			pass
		elif interval == 'year':
			interval = relativedelta(years=1)
		elif interval == 'month':
			interval = relativedelta(months=1)
		elif interval == 'week':
			interval = relativedelta(days=7)
		else:
			print('A correct interval needs to be passed. Valid options are: all, year, month, week.')
			return

		# define slots
		
		if interval == 'all':
			time_slots = 'all'
		else:
			time_slots = []
			while start_date < end_date:
				tmp_start = self.get_wb_date(start_date, start=True)
				time_slots.append(tmp_start)
				start_date = start_date + interval

			tmp_end = self.get_wb_date(end_date, end=True)
			time_slots.append(tmp_end)

		results = self.get(query_url, pattern, time_slots, diversify_all, diversify_intervals, results_per_interval, filter_errors, filter_redirects, filter_revisits)
		results['archive_url'] = results.apply(self.get_archive_url, axis=1)
		results['archive_url_without_timeline'] = results.apply(self.get_clean_archive_url, axis=1)
		results = results[['urlkey', 'archive_url', 'archive_url_without_timeline', 'statuscode', 'mimetype']]

		return results

	def get_archive_url(self, x):
		archive_url = self.archive_root + str(x['timestamp']) + '/' + x['original']
		return archive_url

	def get_clean_archive_url(self, x):
		archive_url = self.archive_root + str(x['timestamp']) + self.timestamp_suffix + '/' + x['original']
		return archive_url


	def get_wb_date(self, date, start=False, end=False):
		tmp_year = str(date.year)
		tmp_month = str(date.month)
		tmp_day = str(date.day)
		if len(tmp_month) == 1:
			tmp_month = '0' + tmp_month
		if len(tmp_day) == 1:
			tmp_day = '0' + tmp_day
		if start:
			result = int(tmp_year+tmp_month+tmp_day+'000000')
		if end:
			result = int(tmp_year+tmp_month+tmp_day+'235959')
		return result
	
	def set_params(self, output=None, limit=None, showResumeKey=None):
		if output:
			self.params['output'] = output
		if limit:
			self.params['limit'] = limit
		if showResumeKey:
			self.params['showResumeKey'] = showResumeKey


