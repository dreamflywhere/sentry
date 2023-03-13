# Generated by Django 2.2.28 on 2023-03-09 23:03

from django.db import migrations

from sentry.new_migrations.migrations import CheckedMigration
from sentry.utils.query import RangeQuerySetWrapperWithProgressBar

DEFAULT_ENVIRONMENT_NAME = "production"


def backfill_monitor_environments(apps, schema_editor):
    Monitor = apps.get_model("sentry", "Monitor")
    Environment = apps.get_model("sentry", "Environment")
    EnvironmentProject = apps.get_model("sentry", "EnvironmentProject")
    MonitorEnvironment = apps.get_model("sentry", "MonitorEnvironment")

    queryset = RangeQuerySetWrapperWithProgressBar(
        Monitor.objects.filter(monitorenvironment__isnull=True).values_list(
            "id", "organization_id", "project_id", "status", "next_checkin", "last_checkin"
        ),
        result_value_getter=lambda item: item[0],
    )

    for monitor_id, organization_id, project_id, status, next_checkin, last_checkin in queryset:
        environment = Environment.objects.get_or_create(
            name=DEFAULT_ENVIRONMENT_NAME, organization_id=organization_id
        )[0]

        EnvironmentProject.objects.get_or_create(
            project_id=project_id, environment=environment, defaults={"is_hidden": None}
        )

        monitorenvironment_defaults = {
            "status": status,
            "next_checkin": next_checkin,
            "last_checkin": last_checkin,
        }

        MonitorEnvironment.objects.get_or_create(
            monitor_id=monitor_id, environment=environment, defaults=monitorenvironment_defaults
        )


class Migration(CheckedMigration):
    # This flag is used to mark that a migration shouldn't be automatically run in production. For
    # the most part, this should only be used for operations where it's safe to run the migration
    # after your code has deployed. So this should not be used for most operations that alter the
    # schema of a table.
    # Here are some things that make sense to mark as dangerous:
    # - Large data migrations. Typically we want these to be run manually by ops so that they can
    #   be monitored and not block the deploy for a long period of time while they run.
    # - Adding indexes to large tables. Since this can take a long time, we'd generally prefer to
    #   have ops run this and not block the deploy. Note that while adding an index is a schema
    #   change, it's completely safe to run the operation after the code has deployed.
    is_dangerous = False

    dependencies = [
        ("sentry", "0379_create_notificationaction_model"),
    ]

    operations = [
        migrations.RunPython(
            backfill_monitor_environments,
            migrations.RunPython.noop,
            hints={
                "tables": [
                    "sentry_monitor",
                    "sentry_monitorenvironment",
                    "sentry_environment",
                    "sentry_environmentproject",
                ]
            },
        ),
    ]
