import csv
targets = {'P01012','A0A8V0XA58','Q9PRS8','A0A8V1A6Y9'}
with open('blast/blastp_gallus_coords.tsv', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for r in reader:
        if r['query_acc'] in targets:
            qlen = int(r['query_len'])
            qcov = (int(r['q_end']) - int(r['q_start']) + 1) / qlen * 100
            print(f"{r['query_acc'][:12]:12s} db={r['subject_db']:12s} id={float(r['pct_identity']):5.1f}% e={r['evalue']:12s} qcov={qcov:5.1f}%  {r['subject_name'][:45]}")
