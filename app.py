from flask import Flask, jsonify, Response
import numpy as np
import time
from typing import List, Dict, Union, Tuple

app = Flask(__name__)

def numerical_integration(lower: float, upper: float, n: int) -> Tuple[float, float]:
    delta_x = (upper - lower) / n
    start_time = time.time()
    x_values = np.linspace(lower, upper, n, endpoint=False)
    heights = np.abs(np.sin(x_values))
    area = np.sum(heights) * delta_x
    time_taken = time.time() - start_time
    return area, time_taken

@app.route('/numericalintegral/<float:lower>/<float:upper>')
def integrate(lower: float, upper: float) -> Response:
    results: List[Dict[str, Union[int, float]]] = []
    n_values = [10, 100, 1000, 10000, 100000, 1000000]
    
    for n in n_values:
        result, time_taken = numerical_integration(lower, upper, n)
        results.append({
            'n': n,
            'result': float(result),
            'time_taken': float(time_taken)
        })
    
    return jsonify({
        'lower_bound': float(lower),
        'upper_bound': float(upper),
        'results': results
    })

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)