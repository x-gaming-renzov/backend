import time
import functools
from datetime import datetime

# Shared storage for nested timings
function_timing_stack = []

def track_runtime(user_id=None, task_id=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Determine dynamic values for user_id and task_id
            resolved_user_id = user_id(*args, **kwargs) if callable(user_id) else user_id
            resolved_task_id = task_id(*args, **kwargs) if callable(task_id) else task_id

            # Start timing
            start_time = time.time()

            # Add function to the timing stack
            function_timing_stack.append((func.__name__, start_time))

            try:
                # Run the original function
                result = func(*args, **kwargs)
            finally:
                # Stop timing
                end_time = time.time()
                elapsed_time = int((end_time - start_time) * 1000)  # in ms

                # Pop the function from the timing stack
                function_name, start_time = function_timing_stack.pop()

                # Prepare the timing breakdown
                prefix = "-" * len(function_timing_stack)
                log_entry = f"{prefix}{function_name} --> {elapsed_time}ms\n"

                # If stack is empty, write to time.txt with additional context
                if not function_timing_stack:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    header = f"Run started at: {timestamp}, User ID: {resolved_user_id}, Task ID: {resolved_task_id}\n"
                    with open("time.txt", "a") as log_file:
                        log_file.write(header)
                        log_file.write(log_entry)
                else:
                    # Otherwise, append to current stack's parent's log
                    with open("time.txt", "a") as log_file:
                        log_file.write(log_entry)

            return result
        return wrapper
    return decorator
