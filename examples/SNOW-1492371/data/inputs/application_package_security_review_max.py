#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import traceback


SF_REGRESS_ROOT = os.getenv('SF_REGRESS_ROOT', None)
SF_REGRESS_DEPLOYMENT_NAME = os.getenv('SF_REGRESS_DEPLOYMENT_NAME', 'reg')
sys.path.insert(0, f"{SF_REGRESS_ROOT}/lib2")
sys.path.append(os.path.abspath(os.path.join(SF_REGRESS_ROOT, "regressions/t_native_apps_provider_platform_trust/src")))

import ddlutils
from native_apps_test_util import comment, hide, run, test, fail
from application_object_test_utils import prepare_dev_stage, prepare_setup_script, APP_OBJECT_DATA_DIR, enable_application_object_parameters, disable_application_object_parameters
from natrust_util import *

setup_script_path = "lookup_app/scripts/version_setup.sql"
conn_sf = ddlutils.get_snowflake_connection()

name_prefix = "NATRUST_"
provider = name_prefix + "provider"
conn_provider = None
scanner = name_prefix + "scanner"
conn_scanner = None

provider_db = "provider_max_db"
provider_schema = "provider_schema"
provider_version_dir = "v1"
provider_stage = "app_files"

app_package = 'app__max_package'
app_version_name = 'V1'

scan_db = 'scan_db'
scan_schema = 'scan_schema'
scan_files_stage = 'files_stage'

def run_test():
    run(conn_sf, f"use warehouse regress")

    # Clean up reviews first
    hide(conn_sf, "SELECT SYSTEM$CLEANUP_APPLICATION_SECURITY_REVIEWS_IN_REQUESTER()")
    run(conn_sf, f"alter account {provider} set MAX_SECURITY_REVIEWS_PER_PACKAGE_VERSION_TOGGLING_EXTERNAL=-1")

    provider_account_id = get_current_account_id(conn_provider)

    run(conn_provider, f"create warehouse wh")
    run(conn_provider, f"create database {provider_db}")
    run(conn_provider, f"create schema {provider_schema}")
    prepare_setup_script(setup_script_path, [f"select 1"])

    run(conn_provider, f'use database {provider_db}')
    run(conn_provider, f'use schema {provider_schema}')
    run(conn_provider, f"create table provider_table (f1 int, f2 varchar, f3 boolean)")
    run(conn_provider, f'CREATE STAGE {provider_stage} encryption = (type = \'SNOWFLAKE_FULL\')')
    app_version_path = f'@{provider_db}.{provider_schema}.{provider_stage}/{provider_version_dir}/'
    prepare_dev_stage(conn_provider, f"{provider_stage}/{provider_version_dir}", "lookup_app", run_with=hide)

    test(conn_provider, f"CREATE APPLICATION PACKAGE {app_package} distribution=internal")
    app_package_id = get_application_package_id(conn_provider, app_package)

    # Create a new version.
    test(conn_provider, f"""
        ALTER APPLICATION PACKAGE {app_package}
        ADD VERSION {app_version_name}
        USING '{app_version_path}'
    """)

    for i in range(10):
        test(conn_provider, f"""
            ALTER APPLICATION PACKAGE {app_package}
            ADD PATCH FOR VERSION {app_version_name}
            USING '{app_version_path}'
        """)

    test(conn_provider, f"SHOW VERSIONS IN APPLICATION PACKAGE {app_package}")

    test(conn_provider, f"ALTER APPLICATION PACKAGE {app_package} SET DEFAULT RELEASE DIRECTIVE VERSION = {app_version_name} PATCH = 3")

    run(conn_sf, f"alter account {provider} set MAX_SECURITY_REVIEWS_PER_PACKAGE_VERSION_TOGGLING_EXTERNAL=3")

    test(conn_provider, f"ALTER APPLICATION PACKAGE {app_package} SET DISTRIBUTION=EXTERNAL")

    test(conn_provider, f"SHOW VERSIONS IN APPLICATION PACKAGE {app_package}")

    # wait for patch 8, 9, 10 to be sent, other are not reviewed
    for i in range(8, 11):
        review = wait_for_requester_review_state(conn_sf, provider_account_id, app_package_id, app_version_name, i, 'PENDING_SCAN', 60)
        comment("PATCH %d:  Review State In Requester: %s" % (i, STATES[review['state']]))

        review = wait_for_scanner_review_state(conn_sf, 1, provider_account_id, app_package_id, app_version_name, i, 'PENDING_SCAN', 60)
        comment("PATCH %d:  Review State In Scanner: %s" % (i, STATES[review['state']]))

    # patch 3 is also sent as its release directive
    review = wait_for_requester_review_state(conn_sf, provider_account_id, app_package_id, app_version_name, 3, 'PENDING_SCAN', 60)
    comment("PATCH %d:  Review State In Requester: %s" % (3, STATES[review['state']]))

    review = wait_for_scanner_review_state(conn_sf, 1, provider_account_id, app_package_id, app_version_name, 3, 'PENDING_SCAN', 60)
    comment("PATCH %d:  Review State In Scanner: %s" % (3, STATES[review['state']]))

    # we can try to send a another patch via retry logic if needed for support reasons
    run(conn_sf, f"""CALL SYSTEM$CREATE_APPLICATION_SECURITY_REVIEW_IN_REQUESTER({provider_account_id},{app_package_id},'{app_version_name}',6)""",
        edits={f"({provider_account_id},": "(<app pkg account id>,",f",{app_package_id},": ",<app pkg id>,"})

    test(conn_provider, f"SHOW VERSIONS IN APPLICATION PACKAGE {app_package}")

    review = wait_for_requester_review_state(conn_sf, provider_account_id, app_package_id, app_version_name, 6, 'PENDING_SCAN', 60)
    comment("PATCH %d:  Review State In Requester: %s" % (6, STATES[review['state']]))

    review = wait_for_scanner_review_state(conn_sf, 1, provider_account_id, app_package_id, app_version_name, 6, 'PENDING_SCAN', 60)
    comment("PATCH %d:  Review State In Scanner: %s" % (6, STATES[review['state']]))

def setup_test():
    global conn_provider, conn_scanner

    conn_provider = ddlutils.get_conn_local(provider)
    conn_scanner = ddlutils.get_conn_local(scanner)

    enable_application_object_parameters(conn_sf, provider)
    enable_application_object_parameters(conn_sf, scanner)

    hide(conn_sf, f"alter account {provider} set ENABLE_APPLICATION_PACKAGE_VERSION_AUTOMATED_SECURITY_REVIEW=true")
    hide(conn_sf, f"alter account {provider} set ENABLE_APPLICATION_PACKAGE_VERSION_TRUST_ENFORCEMENT=true")
    hide(conn_sf, f"alter account {scanner} set ENABLE_SECURITY_REVIEW_SYSTEM_FUNCS=true")

    # Mark the background jobs as enabled at the account-level so that
    # work will be scheduled for them.  This won't start the jobs:
    # that has to be done at the system-level.
    #
    # We use DISABLE_NATIVE_APPS_BG_UPGRADE_FOR_TEST to keep any running
    # jobs from poking at this account while testing.  The SYNC part
    # grabs the locks, ensuring the parameter change is observed.
    #
    hide(conn_sf, f"""
        ALTER ACCOUNT {provider} SET
            enable_native_apps_bg_version_dropper   = true,
            disable_native_apps_bg_upgrade_for_test = true;
    """)
    hide(conn_provider, f"""
        SELECT SYSTEM$INTERNAL_NATIVE_APPS_BG_UPGRADE_CTRL('sync')
    """)


def cleanup():
    hide(conn_provider, f"drop database if exists {provider_db}")
    hide(conn_provider, f"drop database if exists {app_package}")
    hide(conn_provider, f"drop database if exists {app_package}_2")

    hide(conn_provider, f"drop warehouse if exists wh")

    disable_application_object_parameters(conn_sf, provider)
    disable_application_object_parameters(conn_sf, scanner)
    hide(conn_sf, f"alter account {provider} unset ENABLE_APPLICATION_PACKAGE_VERSION_AUTOMATED_SECURITY_REVIEW")
    hide(conn_sf, f"alter account {provider} unset ENABLE_APPLICATION_PACKAGE_VERSION_TRUST_ENFORCEMENT")
    hide(conn_sf, f"alter account {provider} unset MAX_SECURITY_REVIEWS_PER_PACKAGE_VERSION_TOGGLING_EXTERNAL")
    hide(conn_sf, f"""
        ALTER ACCOUNT {provider} UNSET
            enable_native_apps_bg_version_dropper,
            disable_native_apps_bg_upgrade_for_test;
    """)

    hide(conn_sf, "SELECT SYSTEM$CLEANUP_APPLICATION_SECURITY_REVIEWS_IN_REQUESTER()")
    conn_sf.sf_disconnect()

    if os.path.exists(APP_OBJECT_DATA_DIR + setup_script_path):
        os.remove(APP_OBJECT_DATA_DIR + setup_script_path)




def main():
    try:
        setup_test()
        run_test()
    except Exception as e:
        print("TEST FAILURE:", e)
        traceback.print_tb(e.__traceback__)
    finally:
        cleanup()


if __name__ == '__main__':
    main()
