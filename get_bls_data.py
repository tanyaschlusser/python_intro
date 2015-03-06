#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
get_bls_data.py

This pulls data from the BLS
    - useful code: http://www.bls.gov/developers/api_python.htm
    - reference for series IDs http://www.bls.gov/help/hlpforma.htm
"""
import json
import os
import requests  # for HTTP requests and much more
import tablib  # to output data

#------------------------------------------------------ Globals ---#
BLS_API_KEY = '79cdd5c54e0d441383f373bdff87ea0c'
OUT_DIR = "output"
if not os.path.exists(OUT_DIR):
    os.mkdir(OUT_DIR)

#------------------------------------------------------ Setup ---#
def get_data(series_list):
    """Get results from the BLS API query.

    :param series_list: list of series IDs
    :returns: a dictionary parsed from the returned JSON string.
    """
    headers = {'Content-type': 'application/json'}
    url = 'http://api.bls.gov/publicAPI/v1/timeseries/data/'
    data = json.dumps({
            "registrationKey": BLS_API_KEY,
            "seriesid": series_list,
            "startyear": "2011",
            "endyear": "2014"})
    p = requests.post(url, data=data, headers=headers)
    return json.loads(p.text)


#--------------------------------------------------------------------------
# Original way from the BLS page
#
print "Doing the original query..."
series_ids = ['CUUR0000SA0','SUUR0000SA0']
json_data =  get_data(series_ids)

for series in json_data['Results']['series']:
    x=tablib.Dataset(
            headers= ["series id","year",
                      "period","value","footnotes"])
    seriesId = series['seriesID']
    for item in series['data']:
        year = item['year']
        period = item['period']
        value = item['value']
        footnotes=""
        for footnote in item['footnotes']:
            if footnote:
                footnotes = footnotes + footnote['text'] + ','
        if 'M01' <= period <= 'M12':
            x.append([seriesId,year,period,value,footnotes[0:-1]])
    output = open(os.path.join(OUT_DIR, seriesId + '.csv'),'w')
    output.write(x.csv)
    output.close()
    output = open(os.path.join(OUT_DIR, seriesId + '.xlsx'), 'w')
    output.write(x.xls)
    output.close()
    




###########################################################################
# New section with more complicated stuff
#--------------------------------------------------------------------------
# Get the list of codes that make up the series ID
print "setting up to find the new softwares-specific codes"

with open("bls_codes.json") as infile:
    bls_codes = json.loads(infile.read())

def get_codes_containing(d, search_term):
    """Get the elements in a dictionary with values containing the search.

    :param d: dictionary with keys as code strings and
              values as the code descriptions
    :param search_term: string to compare against dictionary values
    :returns: a subset of `d` containing matches to the search term
    """
    search_term = search_term.lower()
    results = {}
    for k,v in d.iteritems():
        if search_term in v.lower():
            results[k] = v
    return results


#--------------------------------------------------------------------------
# Specify my own Series IDs.
#   -  data_type = ['01', '02', '11']
#      (total employees, average weekly hours, and average weekly earnings)
#
# == State ==
# I found the right codes by hand and left the below just so
# you could see how I did it. I could have also just done
#
# state_series = ["", "", ""]
# state_series_names = ["", "", ""]
#
# But then you woudln't get the benefit of all this extra
# mumbidy - jumbidy.
#
# For each dictionary state_dict, area_dict, and industry_dict
# I know from my data exploration by hand that these dictionaries
# each are only one item long
s = bls_codes["State and Area Employment, Hours, and Earnings"]
state_format = s["series_id_format"]
prefix = s["prefix"]
seasonal_adjustment = "U"  # No seasonal adjustment
data_types = ["01", "02", "11"]

state_dict = get_codes_containing(s['state'], 'illinois')
area_dict = get_codes_containing(s['area'], 'statewide')
industry_dict = get_codes_containing(s['supersector_and_industry'], 'software')

state = state_dict.keys()[0]
area = area_dict.keys()[0]
industry = industry_dict.keys()[0]
state_series = []
state_series_names = []
for data_type in data_types:
    state_series_names.append(
        "Software in Illinois, " + s['data_type'][data_type])
    state_series.append(state_format.format(
        prefix=prefix,
        seasonal_adjustment=seasonal_adjustment,
        state=state,
        area=area,
        supersector_and_industry=industry,
        data_type=data_type))

# == National ==
# Almost all of the codes are the same: industry, data_type.
n = bls_codes["National Employment, Hours, and Earnings"]
natl_format = n["series_id_format"]
prefix = n["prefix"]
natl_series = []
natl_series_names = []
for data_type in data_types:
    natl_series_names.append(
        "Software Nationally, " + n['data_type'][data_type])
    natl_series.append(natl_format.format(
        prefix=prefix,
        seasonal_adjustment=seasonal_adjustment,
        supersector_and_industry=industry,
        data_type=data_type))

# == Combine state and national ==
new_series = state_series + natl_series
new_names = state_series_names + natl_series_names
series_name_lookup = dict(zip(new_series, new_names))
filename = "State_and_national_earnings_software_no_seasonal"
footnotes_filename = "Footnotes_" + filename

# This time the table will have each series as a column.
# There will be a second file with all of the footnotes.
print "Getting the new data..."
json_data =  get_data(new_series)

data = {}
all_footnotes = {}

for series in json_data['Results']['series']:
    series_id = series['seriesID']
    for item in series['data']:
        year = item['year']
        period = item['period']
        value = item['value']
        footnotes = ", ".join(f for f in item['footnotes'] if f )
        if 'M01' <= period <= 'M12':
            if year not in data:
                data[year] = {}
            if period not in data[year]:
                data[year][period] = {}
            data[year][period][series_id] = value

            if footnotes:
                if year not in all_footnotes:
                    all_footnotes[year] = {}
                if period not in all_footnotes[year]:
                    all_footnotes[year][period] = {}
                all_footnotes[year][period][series_id] = footnotes


# Get all of the years and periods for the dataset
# as a list of tuples, e.g.
#    [("2011", "M01"), ("2011", "M02"), ... , ("2014", "M12")]
years_and_periods = []
series_columns = dict((s,[]) for s in new_series)
for year in data.keys():
    years_and_periods.extend((year, period) for period in data[year])

# Create separate columns for all of the other datasets we chose
years_and_periods.sort()
for y, p in years_and_periods:
    for series, column in series_columns.iteritems():
        column.append("" if series not in data[y][p] else data[y][p][series])

# Start the dataset with the years and periods, then
# append the series columns one by one.
x = tablib.Dataset(*years_and_periods, headers=("year", "period"))
for series, column in series_columns.iteritems():
    x.append_col(column, header=series_name_lookup[series])

with open(os.path.join(OUT_DIR, filename + ".csv"), "w") as outfile:
    outfile.write(x.csv)


# Write out the footnote
footnote_format = "{year}\t{period}\t{series}\t{note}\n"
with open(os.path.join(OUT_DIR, footnotes_filename + ".txt"), "w") as outfile:
    for year in sorted(all_footnotes.keys()):
        for period in sorted(all_footnotes[year].keys()):
            for series_id in sorted(all_footnotes[year][period].keys()):
                outfile.write(footnote_format.format(
                    year=year,
                    period=period,
                    series=series_name_lookup[series_id],
                    note=all_footnotes[year][period][series_id]))

