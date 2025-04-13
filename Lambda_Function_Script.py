import boto3
from datetime import datetime, timezone, timedelta

# Initialize AWS service clients
ec2 = boto3.client('ec2')
sns = boto3.client('sns')

def lambda_handler(event, context):
    # Fetch all EBS snapshots owned by the current AWS account
    all_snapshots = ec2.describe_snapshots(OwnerIds=['self'])["Snapshots"]

    # Extract snapshot IDs into a list
    snapshots = []
    for snap_id in all_snapshots:
        snapshot_id = snap_id["SnapshotId"]
        snapshots.append(snapshot_id)

    # Extract volume IDs into a list
    volumes = []
    for vol_id in all_snapshots:
        volume_id = vol_id["VolumeId"]
        volumes.append(volume_id)

    # Lists to track snapshots without active volumes and existing volumes
    isolated_snapshots = []
    existing_volumes = []
    
    # Pair each snapshot with its source volume
    zipped_snaps_vols = list(zip(snapshots, volumes))

    # Check each snapshot-volume pair
    for index in zipped_snaps_vols:
        try:
            
            volume_state = ec2.describe_volumes(VolumeIds=[str(index[1])])["Volumes"]
        except:
            # If volume doesn't exist, add snapshot to isolated list
            print("The Volume "+index[1]+" no longer exists !!")
            isolated_snapshots.append(index[0])
            continue

        # Check the state of each volume
        for state in volume_state:
                vol_state = state["State"]
                if vol_state == "in-use":
                    # If volume is in use, get details about the attached EC2 instance
                    ins_id = state["Attachments"]
                    for id in ins_id:
                        instance_id = id["InstanceId"]
                        ec2_instances = ec2.describe_instances(InstanceIds=[instance_id])["Reservations"]
                        for instance in ec2_instances:
                            for id in instance["Instances"]:
                                instance_state= id["State"]["Name"]
                                print("The volume "+index[1]+" is attached to the "+instance_state+" EC2 instance: "+instance_id)
                                existing_volumes.append(index[1])

                if vol_state == "available":
                    # If volume exists but is not attached to any instance
                    print("The volume "+index[1]+" is not attached to any EC2 instance")
                    isolated_snapshots.append(index[0])
                    existing_volumes.append(index[1])

    # Get all AMIs (Amazon Machine Images) owned by the account
    images = ec2.describe_images(Owners=['self'])['Images']

    # Remove snapshots that are used by AMIs from the isolated list
    for snap in isolated_snapshots[:]:
        for img in images:
            mappings = img["BlockDeviceMappings"]
            for id in mappings:
                if "Ebs" in id and "SnapshotId" in id["Ebs"]:
                    snap_id = id["Ebs"]["SnapshotId"]
                    if snap == snap_id and snap in isolated_snapshots:
                        isolated_snapshots.remove(snap)
                        break

    # List for snapshots older than 3 months
    orphaned_snapshots = []
    
    # Define the timestamp for 90 days ago
    three_months_time = datetime.now(timezone.utc) - timedelta(days=90)

    # Check creation date of each isolated snapshot
    for snap in isolated_snapshots:
        snapshots = ec2.describe_snapshots(SnapshotIds=[snap])['Snapshots']
        for snapshot in snapshots:
            start_time = snapshot['StartTime'] 
            if start_time < three_months_time:
                # Snapshot is older than 3 months
                print("The snapshot "+snap+" is older than three months. Created on "+str(start_time))
                orphaned_snapshots.append(snap)
            else:
                # Snapshot is recent (less than 3 months old)
                print("The snapshot "+snap+" is recent. Created on "+str(start_time))
                continue

    # List for snapshots that need review for deletion
    review_snapshots = []

    if not orphaned_snapshots:
        print("No orphaned snapshots to check !!!")
    else:
        # Check if any existing volumes were created from the orphaned snapshots
        for item in orphaned_snapshots:
            response = ec2.describe_volumes(Filters=[
                {
                'Name': 'snapshot-id',
                'Values': [item]
                },
                    ],
                        )["Volumes"]
            if not response:
                # No volumes were created from this snapshot
                print("None of the existing volumes have been created by the snapshot with the ID "+item)
                review_snapshots.append(item)
            else:
                for vol in response:
                    vol_id = vol['VolumeId']
                    create_time = vol['CreateTime']
                    if vol_id in existing_volumes:
                        # Volume created from this snapshot is still in use
                        print("The snapshot "+item+" has been used to create the volume "+vol_id+" on "+create_time)
                    else:
                        # Volume created from this snapshot is no longer in use
                        review_snapshots.append(item)
                        

    # Tag snapshots identified as safe to delete
    for snapshot in review_snapshots:
        try:
            response=ec2.create_tags(
                Resources=[snapshot],
                Tags=[
                    {
                        'Key' : 'SafeToDelete',
                        'Value' : 'true'
                    }
                ]
            )
            print("The snapshot "+snapshot+" has been tagged as SafeToDelete=true")
        except:
            print("Failed to tag the snapshot "+ snapshot)
            continue

    # SNS topic ARN for notifications
    topic_arn = 'arn:aws:sns:us-east-1:442042504085:cw-sns-topic'  # Replace with your topic ARN

    # Format and send notification message based on findings
    if review_snapshots:
        # Snapshots were identified as safe to delete
        message = "The EBS Snapshots with the following Snapshot IDs are safe to delete:\n\n" + "\n".join(review_snapshots)
        response = sns.publish(
            TopicArn=topic_arn,
            Subject="Action Required: Orphaned EBS Snapshots Identified",
            Message=message
        )
    else:
        # No snapshots were marked safe for deletion
        message = "No Snapshots were marked safe for deletion."
        response = sns.publish(
            TopicArn=topic_arn,
            Subject="Results: Orphaned EBS Snapshot Check",
            Message=message
        )

    print("Notification sent! Message ID:", response['MessageId'])

    # Return success response
    return {
            'statusCode': 200,
            'body': 'Lambda function executed successfully'
        }