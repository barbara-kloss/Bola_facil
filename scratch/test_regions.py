import psycopg2
password_encoded = 'b8RDz%23w%3FdHc_f%3Ff'
regions = [
    'sa-east-1', 
    'us-east-1', 
    'us-west-1', 
    'us-west-2', 
    'eu-west-1', 
    'eu-west-2'
]
for r in regions:
    for port in [5432, 6543]:
        try:
            dsn = f'postgresql://postgres.veooiziqewuoolrkrfdf:{password_encoded}@aws-0-{r}.pooler.supabase.com:{port}/postgres'
            conn = psycopg2.connect(dsn)
            conn.close()
            print(f"SUCCESS: {r} on port {port}")
            exit(0)
        except Exception as e:
            err_str = str(e).strip().replace('\n', ' ')
            print(f"FAILED {r} (port {port}): {err_str}")
