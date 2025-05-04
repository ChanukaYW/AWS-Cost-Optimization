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


Step 01: Create the Lambda Function 

	• Crate a Lambda Function with Python as the Runtime
 
	• Add the Python script under the Code section
 
	• Go to Configuration → Permissions → Execution role and click on the Role name
 
	• Click on Add permissions and select Create inline policy
 
	• Choose EC2 as the Service and add the following actions.
 
			§ DescribeImages
			§ DescribeInstances
			§ DescribeSnapshots
			§ DescribeVolumes
			§ CreateTags
   
	• Click Next
 
	• provide a Policy name and click on Create policy (It'll appear under the Permissions policies section, after the basic execution role of your Lambda function)

Step 02: Create SNS Topic

	• Go to the SNS console
 
	• Click Topics → Create topic
 
	• Select Standard type
 
	• Enter a preffered Name
 
	• Click Create topic
 
	• Note the Topic ARN (you'll need this for the Lambda function)
 
	• With your new topic selected, click Create subscription
 
	• For Protocol, select Email
 
	• For Endpoint, enter your preffered email address to receive notifications
 
	• Click Create subscription
 
	• Confirm the subscription from the email you receive

Step 03: Update Lambda Function

	• Go back to your Lambda Function
 
	• Go to Configuration → Permissions → Execution role and click on the Role name
 
	• Click on the inline policy that you created earlier
 
	• Add a new permission by selecting SNS as the service and selecting Publish as the action
 
	• Click on Add ARNs, copy your SNS Topic's ARN and paste it under Resource ARN
 
	• Save the changes to the existing inline policy
 
	• Now go to Configuration →  General configuration
 
	• Click Edit
 
	• Set Timeout to at least 30 seconds
 
	• Click Save

Step 04:  Create EventBridge Rule

	• Go to Amazon EventBridge console
 
	• Click Rules → Create rule
 
	• Enter an appropriate Name
 
	• For Rule type, select Schedule
 
	• Click on Continue in EventBridge Scheduler 
 
	• Select Recurring schedule as the Occurrence of the schedule 
 
	• Define a schedule pattern as per your requirements: 
		○ Ex: To trigger the Lambda function on the 1st of each month: cron(0 0 1 * ? *)
  
	• Select a suitable Flexible time window
 
	• Click Next
 
	• Select AWS Lambda as the Target API
 
	• Select you Lambda function from the dropdown under Invoke
 
	• Click Next until you can create the schedule
 

Step 05: Testing the Solution

	• Go to your Lambda function
 
	• Click on Deploy (Ctrl+Shift+U)
 
	• Click on Test (Ctrl+Shift+I) → Create new test event
 
	• Enter an Event Name and create a new test event with empty JSON: {}

	• Once again, click on Test to run your function manually
 
	• Check CloudWatch Logs to verify function execution
 
	• Verify that you receive the SNS notification email




