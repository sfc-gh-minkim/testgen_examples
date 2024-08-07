import time

import pytest

from snowfort.testlib.annotations.features import FeatureArea
from snowfort.testlib.annotations.isolation import SFIsolationLevel
from snowfort.testlib.annotations.runtime import Runtime
from snowfort.testlib.annotations.sut import SUT
from snowfort.testlib.base_test import BaseTest
from snowfort.testlib.native_apps.annotations.accounts import NativeAppsMultipleAccounts, NativeAppsProviderAccount
from snowfort.testlib.native_apps.api.application_package_api import ApplicationPackageProperty
from snowfort.testlib.native_apps.api.native_apps_api import NativeAppsApi
from snowfort.testlib.native_apps.api.native_apps_sql import NativeAppsSql
from snowfort.testlib.native_apps.api.stage_api import StageEncryption
from snowfort.testlib.native_apps.constants.database_flag import DatabaseFlag
from snowfort.testlib.native_apps.constants.distribution import Distribution
from snowfort.testlib.native_apps.constants.parameters import Parameter
from snowfort.testlib.native_apps.fixtures.security_scanner import SecurityScanner
from snowfort.testlib.native_apps.models.application import Application
from snowfort.testlib.native_apps.models.application_package import ApplicationPackage
from snowfort.testlib.native_apps.models.application_package_security_review import ReviewState
from snowfort.testlib.native_apps.templates.setup_script import SetupScript


@SecurityScanner
@FeatureArea.native_apps
@SUT.local_fs
@Runtime.precommit
@NativeAppsMultipleAccounts.with_args(
    provider=NativeAppsMultipleAccounts.CreationSettings(
        {
            Parameter.ENABLE_NATIVE_APPS_BG_VERSION_DROPPER: True,
            Parameter.DISABLE_NATIVE_APPS_BG_UPGRADE_FOR_TEST: True,
            Parameter.ENABLE_NATIVE_APPLICATION_TRUST_INTEGRATION: True,
            Parameter.ENABLE_APPLICATION_PACKAGE_VERSION_AUTOMATED_SECURITY_REVIEW: True,
            Parameter.ENABLE_APPLICATION_PACKAGE_VERSION_TRUST_ENFORCEMENT: True,
        }
    ),
    scanner=NativeAppsMultipleAccounts.CreationSettings(
        parameters={Parameter.ENABLE_SECURITY_REVIEW_SYSTEM_FUNCS: True},
    ),
)
class TestApplicationPackageSecurityReviewDropping(BaseTest):
    """Migrated from `application_package_security_review_dropping.py`"""

    @pytest.fixture(scope="function")
    def _app_package(self, api: NativeAppsApi, sql: NativeAppsSql) -> ApplicationPackage:
        api.procedure.call("SYSTEM$INTERNAL_NATIVE_APPS_BG_UPGRADE_CTRL", args=["sync"])
        api.procedure.call("SYSTEM$CLEANUP_APPLICATION_SECURITY_REVIEWS_IN_REQUESTER", use_snowflake_connection=True)
        api.listing.accept_provider_monetization_terms()
        api.global_metadata.sync_full()

        stage = api.stage.create(encryption_type=StageEncryption.SNOWFLAKE_FULL)
        api.stage.prepare_app_stage(stage)

        app_package = api.application_package.create()
        api.application_package.add_version(app_package, stage=stage)
        api.application_package.add_patch(app_package, stage=stage)
        api.application_package.add_patch(app_package, stage=stage)
        api.application_package.add_patch(app_package, stage=stage)
        api.application_package.add_patch(app_package, stage=stage)
        api.application_package.alter_set(app_package, {ApplicationPackageProperty.DISTRIBUTION: Distribution.EXTERNAL})
        api.global_metadata.sync_full()
        return app_package

    def test_dropping_application_package_clears_all_reviews(
        self, api: NativeAppsApi, sql: NativeAppsSql, _app_package: ApplicationPackage
    ):
        pkg_id = api.dpo.get_entity_id(_app_package)
        version = _app_package.version
        for patch_id in range(5):
            assert (
                api.application_package_security_review.wait_for_requester_review_state(
                    _app_package, ReviewState.PENDING_SCAN
                ).state
                == ReviewState.PENDING_SCAN
            )
            assert (
                api.application_package_security_review.wait_for_scanner_review_state(
                    _app_package, ReviewState.PENDING_SCAN
                ).state
                == ReviewState.PENDING_SCAN
            )

        api.database.drop(_app_package)
        api.global_metadata.sync_full()

        for patch_id in range(5):
            api.application_package_security_review.wait_for_requester_review_drop(
                package_id=pkg_id, version=version, patch_id=patch_id
            )

        sql.fail("SELECT SYSTEM$CLEANUP_APPLICATION_SECURITY_REVIEWS_IN_REQUESTER()").assert_query_error_result(2140)
        api.procedure.call(
            "SYSTEM$CLEANUP_APPLICATION_SECURITY_REVIEWS_IN_REQUESTER", use_snowflake_connection=True
        ).compare_with_scalar("Stale Reviews cleaned up = 0")

        api.global_metadata.sync_full()

        for patch_id in range(4):
            api.application_package_security_review.wait_for_requester_review_drop(
                package_id=pkg_id, version=version, patch_id=patch_id
            )
