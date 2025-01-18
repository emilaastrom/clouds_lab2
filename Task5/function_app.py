import azure.functions as func
import azure.durable_functions as df
from typing import List, Dict
from urllib.request import urlopen
from operator import itemgetter

myApp = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@myApp.activity_trigger(input_name="context")
def get_input_data(context) -> list:
    input_urls = [
        "https://v2task5.blob.core.windows.net/task5container/mrinput-1.txt",
        "https://v2task5.blob.core.windows.net/task5container/mrinput-2.txt",
        "https://v2task5.blob.core.windows.net/task5container/mrinput-3.txt",
        "https://v2task5.blob.core.windows.net/task5container/mrinput-4.txt"
    ]
    
    input_data = []
    line_number = 0
    
    for url in input_urls:
        with urlopen(url) as response:
            content = response.read().decode('utf-8')
            lines = content.splitlines()
            for line in lines:
                if line.strip():
                    line_number += 1
                    input_data.append((line_number, line))
    
    return input_data

@myApp.activity_trigger(input_name="context")
def mapper(context) -> list:
    _, line = context
    words = [word.strip("'") for word in line.lower().split() if word.strip("'")]
    return [(word, 1) for word in words]

@myApp.activity_trigger(input_name="context")
def shuffler(context) -> dict:
    word_groups = {}
    for mapper_output in context:
        for word, count in mapper_output:
            if word not in word_groups:
                word_groups[word] = []
            word_groups[word].append(count)
    return word_groups

@myApp.activity_trigger(input_name="context")
def reducer(context) -> tuple:
    word, counts = context
    return (word, sum(counts))

def format_results(reduce_results: List[tuple]) -> str:
    sorted_results = sorted(reduce_results, key=lambda x: (-x[1], x[0]))
    total_words = sum(count for _, count in sorted_results)
    
    lines = []
    for word, count in sorted_results:
        percentage = (count / total_words) * 100
        lines.append(f"{word}: {count} ({percentage:.1f}%)")
    
    lines.append(f"Total unique words: {len(sorted_results)}")
    lines.append(f"Total word count: {total_words}")
    
    return " | ".join(lines)

@myApp.orchestration_trigger(context_name="context")
def master_orchestrator(context: df.DurableOrchestrationContext):
    input_data = yield context.call_activity("get_input_data")
    
    map_tasks = []
    for line_num, line in input_data:
        map_tasks.append(context.call_activity("mapper", (line_num, line)))
    map_results = yield context.task_all(map_tasks)
    
    shuffle_results = yield context.call_activity("shuffler", map_results)
    
    reduce_tasks = []
    for word, value_list in shuffle_results.items():
        reduce_tasks.append(context.call_activity("reducer", (word, value_list)))
    reduce_results = yield context.task_all(reduce_tasks)
    
    formatted_output = format_results(reduce_results)
    return formatted_output

@myApp.route(route="orchestrators/{functionName}")
@myApp.durable_client_input(client_name="client")
async def http_start(req: func.HttpRequest, client):
    function_name = req.route_params.get('functionName')
    instance_id = await client.start_new(function_name)
    response = client.create_check_status_response(req, instance_id)
    return response