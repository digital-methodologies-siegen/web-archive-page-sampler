# Simple Python module for retrieving samples of archived webpages in a web archive.
# Copyright (C) 2019 Marcus Burkhardt
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import re
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, Markup

import time_machine as tm



# from app import app
app = Flask('flask_app')


@app.route('/', methods=['GET', 'POST'])
def page():
    search_parameters = ''
    results_headline = ''

    tool_name = 'Web Archive Page Sampler'
    tool_description = Markup(
        f'<p>This tool allows you to create samples of pages within a domain. By default subpages of a domain are included. Uncheck the box "Include Subpages" to retrieve only exact matches.</p>'
        f'<p>You can choose between the sampling intervals: year, month and week. For each intervals the desired number of samples are retrieved.</p>'
        f'<p>By selecting "Diversify Sample" an archived version of unique page is included in each interval only once. By selecting "Diversify Results" an archived version of unique page is included in the results only once.</p>')

    query = request.form.get('query', '')
    include_subdomains = request.form.get('include_subdomains', '')
    include_subpages = request.form.get('include_subpages', '')
    interval = request.form.get('interval', '')
    start_date = request.form.get('start_date', '')
    end_date = request.form.get('end_date', '')
    results_per_interval = request.form.get('results_per_interval', '')
    pattern = request.form.get('pattern', '')
    diversify = request.form.get('diversify', '') 

    
    if not results_per_interval:
        results_per_interval=10
    
    ia = tm.Archive()

    fnp1 = datetime.now().strftime('%Y%m%d-%H%M%S')
    fnp2 = re.sub(r'\W', '_', query if query else '_')
    fnp3 = re.sub(r'\W', '_', interval if interval else '_')
    fnp4 = re.sub(r'\W', '_', str(results_per_interval) if results_per_interval else '_')
    fnp5 = re.sub(r'\W', '_', 'subpages_included' if include_subpages else '_')
    fnp6 = re.sub(r'\W', '_', diversify if diversify else '_')
    fnp7 = re.sub(r'\W', '_', start_date if start_date else '_')
    fnp8 = re.sub(r'\W', '_', end_date if end_date else '_')
    csv_file_name = f'was-{fnp1}-{fnp2}-{fnp3}-{fnp4}-{fnp5}-{fnp6}-{fnp7}-{fnp8}.csv'

    outpath = os.path.join('static', 'downloads')

    if not os.path.isdir(outpath):
        os.makedirs(outpath)

    csv_download_link = os.path.join(outpath, csv_file_name)

    
    
    if query:
        if include_subpages:
            include_subpages=True
        else:
            include_subpages=False

        if diversify:
            if diversify == 'diversify_all':
                diversify_intervals = False
                diversify_all = True
            elif diversify == 'diversify_sample':
                diversify_intervals = True
                diversify_all = False
        else:
            diversify_intervals = False
            diversify_all = False
        results = ia.query(query, include_subpages=include_subpages, interval=interval, diversify_intervals=diversify_intervals, 
            diversify_all=diversify_all, results_per_interval=int(results_per_interval), start_date=start_date,
            end_date=end_date)
        
        search_parameters = Markup(
            f'<p>Search parameters:</p><ul>'
            f'<li>Search query: {query}</li>'
            f'<li>Include Subpages: {include_subpages}</li>'
            f'<li>Interval: {interval}</li>'
            f'<li>Diversify Sample: {diversify_intervals}</li>'
            f'<li>Diversify All: {diversify_all}</li>'
            f'<li>results_per_interval: {results_per_interval}</li>'
            f'<li>Start date: {start_date}</li>'
            f'<li>End date: {end_date}</li></ul>')

    else:
        results = None


    if type(results) == pd.DataFrame:
        results.to_csv(csv_download_link, sep='\t', index=None)
        results_view = f'{len(results)} samples retrieved.'
        csv_download_link = Markup(
            f'<p><a href="{csv_download_link}">Download results.</a></p>')

    else:
        results_view = ''
        csv_download_link = ''

    if type(results) == pd.DataFrame or len(search_parameters) > 0:
        results_headline = Markup('<h3>Results</h3>')

    return render_template(
        'web-archive-page-sampler.html', tool_name=tool_name, tool_description=tool_description, query=query, 
        include_subdomains=include_subdomains, include_subpages=include_subpages, interval=interval, 
        start_date=start_date, end_date=end_date, results_per_interval=results_per_interval, 
        diversify=diversify, results_headline=results_headline,
        results=results_view, search_parameters=search_parameters,
        csv_download_link=csv_download_link)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8048)
