import logging

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Lambda handler function
def lambda_handler(event, context):
	logger.debug('Request event: {}'.format(event))
	
	# Generate response
	response = {
		'uid': 'Called by: {}'.format(event['fun']),
		'email': 'Received Parameters: Next={}, Limit={}'.format(event['parameters']['next'], event['parameters']['limit']),
		'phone': 'Response from test.lambda_handler()'
	}
	logger.debug('JSON Response: {}'.format(response))
	return response
