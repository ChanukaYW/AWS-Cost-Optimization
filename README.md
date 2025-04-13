# Cloud Cost Optimization with Serverless EBS Snapshot Management Solution


This Lambda function identifies and tags unused EBS snapshots that are safe to delete. Here's a summary of what it does:

	• Fetches all EBS snapshots owned by the AWS account
 
	• Identifies snapshots whose source volumes no longer exist or are unattached
 
	• Excludes snapshots that are being used by AMIs (Amazon Machine Images)
	• Filters for snapshots older than 90 days
 
	• Verifies that no existing volumes were created from these snapshots
 
	• Tags qualifying snapshots with "SafeToDelete=true"
 
	• Sends an SNS notification with the list of snapshots safe to delete
	
The script implements a cleanup process that helps maintain your AWS environment by identifying orphaned snapshots that are likely unnecessary, saving on storage costs while ensuring important snapshots aren't deleted.


