import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()


dune_api_keys = [
    os.getenv("DUNE_API_KEY")
]
dune_api_keys = [key for key in dune_api_keys if key]


query_ids = [

    7595582

]

# Create 1:1 mapping between queries and API keys
query_to_key = {query_ids[i]: dune_api_keys[i] for i in range(min(len(query_ids), len(dune_api_keys)))}

print(f"🚀 Starting with {len(dune_api_keys)} API keys available")
print(f"📊 Mapped {len(query_to_key)} queries to dedicated API keys\n")

def get_headers_for_query(query_id):
    """Get headers with the specific API key for this query"""
    api_key = query_to_key.get(query_id)
    if not api_key:
        raise Exception(f"No API key mapped for query {query_id}")
    key_index = list(query_to_key.values()).index(api_key) + 1
    return {"X-DUNE-API-KEY": api_key}, key_index

def execute_queries(query_list):
    """Execute queries using their dedicated API keys"""
    execution_ids = {}
    
    for query_id in query_list:
        url = f"https://api.dune.com/api/v1/query/{query_id}/execute"
        headers, key_num = get_headers_for_query(query_id)
        
        response = requests.post(url, headers=headers)
        result = response.json()
        
        # Check for errors
        if response.status_code in [429, 402] or 'credit' in str(result.get('error', '')).lower():
            print(f"❌ Query {query_id}: API key #{key_num} out of credits - {result.get('error', 'Unknown error')}")
            raise Exception(f"API key #{key_num} for query {query_id} has run out of credits")
        
        # Success
        execution_ids[query_id] = result.get("execution_id")
        print(f"✓ Query {query_id} started: {execution_ids[query_id]} (using dedicated key #{key_num})")
            
    return execution_ids

def poll_until_complete(execution_ids):
    """Poll status every 30 seconds and return failed queries"""
    failed_queries = []
    completed_queries = []
    
    while execution_ids:
        time.sleep(30)
        
        for query_id in list(execution_ids.keys()):
            execution_id = execution_ids[query_id]
            status_url = f"https://api.dune.com/api/v1/execution/{execution_id}/status"
            headers, key_num = get_headers_for_query(query_id)
            
            response = requests.get(status_url, headers=headers)
            
            # Check for credit limit during polling
            if response.status_code in [429, 402]:
                print(f"❌ Query {query_id}: API key #{key_num} out of credits during polling")
                raise Exception(f"API key #{key_num} for query {query_id} exhausted during polling")
            
            status = response.json()
            print(f"Query {query_id} (key #{key_num}): {status['state']}")
            
            if status.get("is_execution_finished"):
                if status['state'] == "QUERY_STATE_COMPLETED":
                    print(f"✅ Query {query_id} SUCCESS")
                    completed_queries.append(query_id)
                elif status['state'] == "QUERY_STATE_FAILED":
                    print(f"❌ Query {query_id} FAILED: {status.get('error', 'Unknown error')}")
                    failed_queries.append(query_id)
                else:
                    print(f"⚠️ Query {query_id} FINAL STATE: {status['state']}")
                    completed_queries.append(query_id)
                
                del execution_ids[query_id]
    
    return failed_queries, completed_queries

# Main execution loop
all_queries = query_ids.copy()
failed_queries = all_queries.copy()

max_retries = 5
retry_count = 0

while failed_queries and retry_count < max_retries:
    if retry_count > 0:
        print(f"\n🔄 Retry attempt {retry_count}/{max_retries}")
    
    print(f"\n{'='*50}")
    print(f"Executing {len(failed_queries)} queries")
    print(f"{'='*50}\n")
    
    try:
        execution_ids = execute_queries(failed_queries)
        
        print(f"\n{'='*50}")
        print(f"Polling for completion...")
        print(f"{'='*50}\n")
        
        failed_queries, completed = poll_until_complete(execution_ids)
        
        if failed_queries:
            print(f"\n⚠️ {len(failed_queries)} queries failed: {failed_queries}")
            retry_count += 1
        else:
            print(f"\n✅ All {len(all_queries)} queries completed successfully!")
            break
            
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        print("Stopping execution.")
        exit(1)

if failed_queries:
    print(f"\n❌ FINAL: {len(failed_queries)} queries failed after {max_retries} retries")
    print(f"Failed queries: {failed_queries}")
    exit(1)

