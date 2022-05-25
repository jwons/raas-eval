import os
import sqlite3
import json
import requests
import re
import matplotlib

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np

from glob import glob

# This function is used to take the processed filename-friendly version of
# a dataset's DOI and return the original DOI
def get_doi_from_filename(filename):
    filename = filename[2:len(filename)]
    doi = os.path.split(filename)[0]
    doi = doi.replace("-", ":", 1)
    doi = doi.replace("-", "/")
    return(doi)


def get_doi_from_dir_path(dir_path):
    doi = dir_path.split("datasets/")[1]
    doi = doi.replace("-", ":", 1)
    doi = doi.replace("-", "/")
    return(doi)



# This function is used when viewing the results of this analysis in the notebook
def print_error_breakdown(error_type, error_dict, num_of_errors):
    print(error_type + " errors: " + str(error_dict[error_type]) + ", or " + str((error_dict[error_type] / num_of_errors) * 100) + "% of total errors")
    
# This function takes a report dictionary and then returns a dictionary with three elements:
# "Errors": The number of scripts in the dataset that ran and encountered an error
# "No Errors": The number of scripts in the dataset that ran and did NOT encounter an error
# "Container-Wide": A boolean indicating whether or not all scripts in the dataset ran WITHOUT errors
def check_errors(report):
    no_errors = True
    num_errorless = 0
    num_errored = 0
    error_causes = []
    
    for script in report["Individual Scripts"]:
        if(len(report["Individual Scripts"][script]["Errors"]) > 0):
            no_errors = False
            #print(report["Individual Scripts"][script]["Errors"])
            num_errored += 1
            error_cause = determine_error_cause(report["Individual Scripts"][script]["Errors"][0])
            error_causes.append((error_cause, os.path.basename(script), report["Individual Scripts"][script]["Errors"][0]))
        else:
            num_errorless += 1
            error_causes.append(("success", os.path.basename(script), "success"))
    return({"Errors": num_errored, "No Errors": num_errorless, "Container-Wide": no_errors, "Error Causes": error_causes})



# Given a dictionary that has broken down datasets and their errors by subject or year, return a dataframe 
def create_breakdown_df(thing_breakdown, name):
    for thing in thing_breakdown.keys():
        thing_breakdown[thing]["percent"] = str(round((thing_breakdown[thing]["errors"] / thing_breakdown[thing]["total"]) * 100, 1)) + "%"
    breakdown_df = pd.DataFrame(thing_breakdown).transpose()
    breakdown_df.index.name = name
    breakdown_df.reset_index(level=0, inplace=True)
    breakdown_df = breakdown_df[[name, "total", "errors", "percent"]]
    breakdown_df.columns = [name, "Total Files", "Total Error Files", "Error Rate (Rounded)"]
    return(breakdown_df)

# Used to replace the last instance of a string character 
# Pulled from https://www.tutorialspoint.com/How-to-replace-the-last-occurrence-of-an-expression-in-a-string-in-Python
# on March 24, 2021
def rreplace(s, old, new):
    return (s[::-1].replace(old[::-1],new[::-1], 1))[::-1]

# Given a dataframe, write its contents to the results directory 
def write_tex_from_df(filename, df, caption = None, label = None, index = False, na_rep = "NaN", escape = True):
    df_latex = df.to_latex(index= index, caption = caption, label = label, na_rep = na_rep, escape = escape)
    df_latex = df_latex.replace("\\\n", "\\ \hline\n")
    df_latex = df_latex.replace("\\ \hline\n", "\\\n", 1)
    df_latex = rreplace(df_latex, "\\ \hline\n", "\\\n")
    with open("../results/" + filename, "w") as outfile:
        outfile.write(df_latex)

def library_name_from_error(error_msg):
    expr = ""
    if("Error in library" in error_msg):
        expr = "library\s*\(\"?([^\"]*)\"?\)"
    elif("there is no package called"):
        expr = "\‘(.*?)\’"
        
    lib_re = re.compile(expr)
    ret_val = None
    try:
        ret_val = lib_re.search(error_msg).groups()[0]
    except:
        ret_val = re.split("\"|\'", error_msg)[1]
    not_packages = ["packages_needed[i]", "pkg", "x", "p", "lib", "package_name", "package"]
    if("," in ret_val and ret_val.split(",")[0] not in not_packages):
        ret_val = ret_val.split(",")[0]
    elif"," in ret_val and ret_val.split(",")[0] in not_packages:
        ret_val = "__UNDEFINED__"
    return(ret_val.replace(" ", ""))


#=================================================

def strip_newlines(doi):
    return(doi.strip("\n"))
strip_newlines_v = np.vectorize(strip_newlines)

def write_file_from_string(filename, to_write):
    with open("../results/" + filename, "w") as outfile:
        outfile.write(to_write)
        
def get_doi_from_results_filename(filename):
    doi = filename.split("/")[3]
    doi = doi.replace("-", ":", 1)
    doi = doi.replace("-", "/")
    return(doi)
get_doi_from_results_filename_v = np.vectorize(get_doi_from_results_filename)

def get_doi_from_tag_name(image_tag):
    return(image_tag[6:9] + image_tag[9:len(image_tag)].replace("-", ":", 1).upper().replace("-", "/"))

def get_doi_from_report(report):
    report_dict = json.loads(report)
    return(get_doi_from_tag_name(report_dict["Additional Information"]["Container Name"]))
get_doi_from_report_v = np.vectorize(get_doi_from_report)

def get_time_from_report(report):
    report_dict = json.loads(report)
    return(report_dict["Additional Information"]["Build Time"])
get_time_from_report_v = np.vectorize(get_time_from_report)

def create_script_id(doi, filename):
    return(doi + ":" + os.path.basename(filename).lower())
create_script_id_v = np.vectorize(create_script_id)

# This function categorizes error messages by searching for the most unique and common phrases in different types of R error messages
def determine_error_cause(error_msg):
    ret_val = "other"
    if(error_msg == "success"):
        ret_val = error_msg
    elif(error_msg == "timed out"):
        ret_val = error_msg
    elif("Error in setwd" in error_msg):
        ret_val = "working directory"
    elif("Error in library" in error_msg):
        ret_val = "library"
    elif("Error in file" in error_msg):
        ret_val = "missing file"
    elif("unable to open" in error_msg):
        ret_val = "missing file"
    elif("Error in readChar" in error_msg):
        ret_val = "missing file"
    elif("could not find function" in error_msg):
        ret_val = "function"
    elif("there is no package called" in error_msg):
        ret_val = "library"
    elif("cannot open the connection" in error_msg):
        ret_val = "missing file"
    return(ret_val)
determine_error_cause_v = np.vectorize(determine_error_cause)

# Download metadata of a doi from a dataset
def get_dataset_metadata(doi, api_url="https://dataverse.harvard.edu/api/"):
    '''
    problem_set = set(["doi:10.7910/DVN/I6H7L5\n",
                       "doi:10.7910/DVN/IBY3PN\n",
                       "doi:10.7910/DVN/NEIYVD\n",
                       "doi:10.7910/DVN/HVY5GR\n",
                       "doi:10.7910/DVN/HVY5GR\n",
                       "doi:10.7910/DVN/UPL4TT\n",
                       "doi:10.7910/DVN/65XKJO\n",
                       "doi:10.7910/DVN/VUHAXF\n",
                       "doi:10.7910/DVN/0WAEAM\n",
                       "doi:10.7910/DVN/PJOMF1\n"])
    # This data has to be hard-coded later. Not sure why, these always time out
    if doi in problem_set:
        print("Skipping problematic dataset")
        return (False,False)
    '''
    api_url = api_url.strip("/")
    subject = None
    year = None
    num_files = None
    timeout_duration = 7
    timeout_limit = 4
    attempts = 0
    while (attempts < timeout_limit):
        try:
            request = requests.get(api_url + "/datasets/:persistentId",
                             params={"persistentId": doi}).json()
            if(request["status"] == "ERROR"):
                print("Possible incorrect permissions for " + doi)
                return (False, False)
            # query the dataverse API for all the files in a dataverse
            files = request['data']
        except requests.exceptions.ReadTimeout as e:
            attempts += 1
            if(attempts == timeout_limit):
                print("Timed-out too many times. Check internet connection?")
                print(doi)
                with open("../data/metadata_problem.txt", "a") as meta_prob:
                    meta_prob.write(doi + " timeout\n")
                return (False, False)
            else:    
                print("Timeout hit trying again")
                continue
        except Exception as e:
            print("Could not get dataset info from dataverse")
            print(e)
            with open("../data/metadata_problem.txt", "a") as meta_prob:
                meta_prob.write(doi + " " + e + "\n")
            return (False, False)
        break
        
    
    year = files["publicationDate"][0:4]
    if("latestVersion" not in files):
        print("latestVersion issue")
        print(doi)
    else:
        for field in files["latestVersion"]["metadataBlocks"]["citation"]["fields"]:
            if(field["typeName"] == "subject"):
                subject = field["value"]

    return(subject, year)

def is_clean(doi, scripts_df):
    ret_val = None
    doi_df = scripts_df[scripts_df["doi"] == doi]
    if len(doi_df.index) > 0:
        ret_val = False
        errors = set(doi_df["nr_error"].values)
        if "success" in errors and len(errors) == 1:
            ret_val = True
    return ret_val