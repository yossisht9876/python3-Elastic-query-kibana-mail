#!/usr/bin/python3

import os
import json
import requests
import base64
import csv
import sys
import pandas as pd
from pandas.io.json import json_normalize
import random
import numpy as np
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
#
# query elasticsearch for android errors
#
def search_android(uri, token, query_android):
  try:
      response = requests.get(uri, headers=token, params=query_android)
      results = json.loads(response.text)
      print (response)

  except requests.exceptions.RequestException as e:
      print(e)
  if response.status_code == 200:
      print(json.dumps(results, sort_keys=False, indent=4))

  else:
      print("faild")
      sys.exit(1)
#
# query elasticsearch for IOS errors
#
def search_ios(uri, token, query_ios):
  try:
     response1 = requests.post(uri, data=json.dumps(query_ios), headers=token)
     results1 = json.loads(response1.content.decode())
     print(response1)
     print(results1)
  except requests.exceptions.RequestException as e:
     print(e)
  if response1.status_code == 200:
       print(json.dumps(results1, sort_keys=False, indent=4))
  else:
       print("faild")
#
#dump elasticserach query results to a json format file
#
def dump_to_file_android(results, response):
  try:
      jsonfile = open('/tmp/android.json', 'w')

      print(json.dumps(results, sort_keys=False, indent=4), file=jsonfile)

      jsonfile.close()
  except requests.exceptions.RequestException as e:
      print(e)

def dump_to_file_ios(results1, response1):
      try:
          jsonfile_ios = open('/tmp/ios.json', 'w')

          print(json.dumps(results1, sort_keys=False, indent=4), file=jsonfile_ios)

          jsonfile_ios.close()
      except requests.exceptions.RequestException as e:
          print(e)
#
# convert the json results file to csv with specipic fields
#
def convert_to_csv_android(results):
  try:
      for i in range(10):
          df = pd.DataFrame([results["hits"]["hits"][i]['_source']], columns=['sdk_version', 'error_message'],index=[i])
          df = df.replace('\n', ' ', regex=True)
          df.to_csv('/tmp/10_android_errors.csv', mode='a', encoding='utf-8', index=False, header=False)
          print(df)

  except requests.exceptions.RequestException as e:
      print(e)

def convert_to_csv_ios(results1):
      try:
          for i in range(10):
              df = pd.DataFrame([results1["aggregations"]["reaons"]["buckets"]], columns=['sdk_version', 'key', 'BundleId', 'doc_count_error_upper_bound' ,"sum_other_doc_count" ],index=[i])
              df = df.replace('\n', ' ', regex=True)
              df.to_csv('/tmp/10_ios_errors.csv', mode='a', encoding='utf-8', index=False, header=False)
              print(df)

      except requests.exceptions.RequestException as e:
          print(e)
#
# send the results as attachment by mail
#
def send_by_mail(fromaddr, toaddr):
    try:
        msg = MIMEMultipart()

        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg['Subject'] = "error log"

        body = "----Daily Report ----\n 10 Most Android_Errors"

        msg.attach(MIMEText(body, 'plain'))

        filename = "10_android_errors.csv",
        filename1 = "10_ios_error.csv"
        flist = ['/tmp/10_android_errors.csv', '/tmp/10_ios_errors.csv']
        for f in flist:
          attachment = open("/tmp/10_android_errors.csv", "rb")
          attachment1 = open("/tmp/10_ios_errors.csv", "rb")
          part = MIMEBase('application', 'octet-stream')
          part.set_payload((attachment).read())
          encoders.encode_base64(part)
          part.add_header('Content-Disposition', ("attachment; filename= %s" % flist))
          #part.add_header('Content-Disposition', ("attachment; filename= %s" % filename1))

          msg.attach(part)

          server = smtplib.SMTP('your smtp server', 25)
#server.starttls()
#server.login(fromaddr, "")
          text = msg.as_string()
          server.sendmail(fromaddr, toaddr, text)
          server.quit()
    except requests.exceptions.RequestException as e:
        print(e)

#
#delete the results files after it was send by mail
#
def delete_result_file():
    try:
        os.remove("/tmp/10_android_errors.csv")

    except requests.exceptions.RequestException as e:
        print(e)


def main():

  uri = "https://coralogix-esapi.coralogix.com:9443/*/_search"
  token = {'token': 'xxxxxxxxxxxxxxxxx', 'Content-Type': 'application/json'}
  query_android = {"q": {"bool": {"filter": [{"terms": {"coralogix.metadata.severity": [5, 6]}}, {"range": {"coralogix.timestamp": {"gte": "now-1d", "lt": "now"
          }}}, {"term": {"Platform.keyword": "android"}},{"term": {"exists": "error_message.keyword"}}, ],"aggs": {"reaons": {"terms": {"field": "error_message.keyword"},
          "aggs": {"sdk_version": {"terms": {"field": "sdk_version.keyword"}}}}}}}}
  query_ios = {"size": 0, "query": {"bool": {"filter": [{"terms": {"coralogix.metadata.severity": [5, 6]}},{"range": {"coralogix.timestamp": {"gte": "now-1d","lt": "now"}}
            },{"term": {"Platform.keyword": "ios"}},{"exists": {"field": "Reason.keyword"}}]}},"aggs": {"reaons": {"terms": {"field": "Reason.keyword"
            },"aggs": {"sdk_version": {"terms": {"field": "SdkVersion.keyword"}},"bundleId": {"terms": {"field": "BundleId.keyword"}}}}}}
  response = requests.get(uri, headers=token, params=query_android)
  response1 = requests.post(uri, data=json.dumps(query_ios), headers=token)
  results = json.loads(response.text)
  results1 = json.loads(response1.content.decode())
  androidjson = '/tmp/android.json'
  data = json.dumps(androidjson)
  fromaddr = "from email"
  toaddr = 'to email'
  search_android(uri, token, query_android)
  search_ios(uri, token, query_ios)
  dump_to_file_android(results, response)
  dump_to_file_ios(results1, response1)
  convert_to_csv_android(results)
  convert_to_csv_ios(results1)
  send_by_mail(fromaddr, toaddr)
  delete_result_file()
if __name__ == "__main__":
    main()
