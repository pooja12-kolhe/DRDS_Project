import requests
from django.conf import settings


def send_sms(to, message):
    try:
        # Remove +91 or 91 prefix, keep only 10 digit number
        number = to.replace('+91', '').replace('91', '').strip()

        response = requests.post(
            'https://www.fast2sms.com/dev/bulkV2',
            headers={'authorization': settings.FAST2SMS_API_KEY},
            data={
                'message': message,
                'language': 'english',
                'route': 'q',
                'numbers': number,
            }
        )

        result = response.json()
        print(f"Fast2SMS Response: {result}")

        if result.get('return') == True:
            print(f"✅ SMS sent to {number}")
            return True
        else:
            print(f"❌ SMS FAILED: {result}")
            return False

    except Exception as e:
        print(f"❌ SMS ERROR: {e}")
        return False
