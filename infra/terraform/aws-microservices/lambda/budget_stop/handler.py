"""Stop billable microservices when AWS Budget SNS alert fires."""
import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ecs = boto3.client("ecs")
rds = boto3.client("rds")
ec2 = boto3.client("ec2")

CLUSTER = os.environ["ECS_CLUSTER"]
RDS_ID = os.environ.get("RDS_INSTANCE_ID", "")
STOP_EC2_TAG_KEY = os.environ.get("STOP_EC2_TAG_KEY", "Project")
STOP_EC2_TAG = os.environ.get("STOP_EC2_TAG", "beauty-store")


def _scale_ecs_to_zero() -> int:
    count = 0
    token = None
    while True:
        kwargs = {"cluster": CLUSTER, "maxResults": 100}
        if token:
            kwargs["nextToken"] = token
        resp = ecs.list_services(**kwargs)
        for arn in resp.get("serviceArns", []):
            name = arn.rsplit("/", 1)[-1]
            ecs.update_service(cluster=CLUSTER, service=name, desiredCount=0)
            logger.info("ECS scaled to 0: %s", name)
            count += 1
        token = resp.get("nextToken")
        if not token:
            break
    return count


def _stop_rds() -> None:
    if not RDS_ID:
        return
    try:
        rds.stop_db_instance(DBInstanceIdentifier=RDS_ID)
        logger.info("RDS stop requested: %s", RDS_ID)
    except rds.exceptions.InvalidDBInstanceStateFault:
        logger.info("RDS already stopped or stopping: %s", RDS_ID)
    except Exception:
        logger.exception("RDS stop failed for %s", RDS_ID)


def _stop_ec2_by_project_tag() -> int:
    if not STOP_EC2_TAG:
        return 0
    ids = []
    for page in ec2.get_paginator("describe_instances").paginate(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    ):
        for res in page.get("Reservations", []):
            for inst in res.get("Instances", []):
                tags = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}
                val = tags.get(STOP_EC2_TAG_KEY, "")
                if STOP_EC2_TAG in val:
                    ids.append(inst["InstanceId"])
    if ids:
        ec2.stop_instances(InstanceIds=ids)
        logger.info("EC2 stop requested: %s", ids)
    return len(ids)


def handler(event, context):
    logger.info("Budget alert event: %s", json.dumps(event)[:2000])
    ecs_count = _scale_ecs_to_zero()
    _stop_rds()
    ec2_count = _stop_ec2_by_project_tag()
    msg = (
        f"Auto-stop complete: {ecs_count} ECS services scaled to 0, "
        f"RDS={RDS_ID or 'n/a'}, EC2 stopped={ec2_count}. "
        "ALB and ElastiCache still bill until terraform destroy."
    )
    logger.info(msg)
    return {"ok": True, "message": msg}
