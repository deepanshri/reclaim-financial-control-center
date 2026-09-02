from pathlib import Path
import csv
ROOT=Path(__file__).parent
def load(n):
    with (ROOT/n).open(newline='',encoding='utf-8') as f: return list(csv.DictReader(f))
p=load('payments.csv'); r=load('refunds.csv'); a=load('anomalies.csv'); q=load('recovery_requests.csv')
hero=[x for x in p if x['anomaly_type']=='fee_rate_increase']
assert len(hero)==1248
assert round(sum(int(x['amount']) for x in hero)/100,2)==2490000.00
assert round(sum(int(x['amount']) for x in hero)/100*0.005,2)==12450.00
assert len({x['id'] for x in p})==len(p)
assert round(sum(float(x['amount_recovered']) for x in q),2)==16650.00
print('VALIDATION PASSED')
