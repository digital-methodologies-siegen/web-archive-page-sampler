import time_machine as tm
ia = tm.Archive()
q = 'www.uni-siegen.de'
results = ia.query(q, interval='month', diversify_intervals=True, results_per_interval=10)
print(results)
