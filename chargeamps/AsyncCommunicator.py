import asyncio
import time

class AsyncCommunicator:
    def __init__(self, call, loop):
        self.loop = loop
        self.call = call

    def blocking_call(self, req):
        task = asyncio.run_coroutine_threadsafe(self.call(req), self.loop)
        while not task.done():
            time.sleep(0.1)  # schedule other threads
        return task.result()
