import sys
import numpy as np
import random
from datetime import datetime
sys.path.append("<kapacitor_library>")
sys.path.append("<implementation>")

from kapacitor.udf.agent import Agent, Handler
from kapacitor.udf import udf_pb2
import logging
import screen

#output the logs in kapacitor
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(name)s: udf: %(message)s')
logger = logging.getLogger()

class ScreenHandler(Handler):
  def __init__(self, agent):
    self.agent = agent

  def info(self):
    response = udf_pb2.Response()
    response.info.wants = udf_pb2.BATCH
    response.info.provides = udf_pb2.BATCH
    return response

  #kapacitor can give aditional paramaeters via init. We don t need any
  def init(self, init_req):
    response = udf_pb2.Response()
    response.init.success = True
    return response

  def snapshot(self):
    response = udf_pb2.Response()
    response.restore.success = False
    response.restore.error = 'not implemented'
    return response

  def restore(self):
    response = udf_pb2.Response()
    response.restore.success = False
    response.restore.error = 'not implemented'
    return response

  def begin_batch(self, begin_req):
    self.matrix = []
    self.begin_req = begin_req  
    self.timestamps = []
    logger.info("begin batch")
    self.initial_time = datetime.now()

  def point(self, point):
    columns = len(point.fieldsDouble)
    current_point = np.zeros(columns)
    for v in range(columns):
      current_point[v] = point.fieldsDouble["dim"+str(v)]
    self.timestamps.append(point.time / 1000000000)
    self.matrix.append(current_point)
  
  def end_batch(self, end_req):
    response = udf_pb2.Response()
    #send back a begin batch to kapacitor
    response.begin.CopyFrom(self.begin_req)
    self.agent.write_response(response)
    
    self.matrix = np.array(self.matrix)

    start_time = datetime.now()
    results = screen.screen(self.matrix, self.timestamps, 0.1, -0.1, 300)
    end_time = datetime.now()
    t = (end_time - start_time).total_seconds()
    response = udf_pb2.Response()
    response.point.fieldsDouble["Screentime"] = t
    #seting timestamp for screen time
    response.point.time = int((datetime.now() - datetime(1970,1,1)).total_seconds() * 1000000000)
    self.agent.write_response(response)

    #29 feb for screeen
    time = 1583000000000000000
    for v in results:
      time = time + 10000000000
      response = udf_pb2.Response()
      response.point.time = time
      for i in range(len(v)):
        response.point.fieldsDouble["dim" + str(i)] = v[i]
      self.agent.write_response(response)
 
    response = udf_pb2.Response()
    response.end.CopyFrom(end_req)
    self.agent.write_response(response)
    logger.info("end batch")
    self.final_time = datetime.now()

    output_file = open("<output_file>", "a")
    output_file.write(str(self.matrix.shape) + " -- " + str((self.final_time - self.initial_time).total_seconds()) + "\n")

if __name__ == '__main__':
  agent = Agent()
  handler = ScreenHandler(agent)
  agent.handler = handler

  logger.info('Starting agent for Screen')
  agent.start()
  agent.wait()
  logger.info('Screen agent finished')
