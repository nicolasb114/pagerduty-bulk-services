#!/usr/bin/env python3
"""
PagerDuty Bulk Service Creator
Creates multiple PagerDuty services from a CSV file with retry logic and failure reporting.
Uses only built-in Python libraries (no external dependencies required).
"""

import csv
import json
import time
import sys
from typing import List, Dict, Tuple
import urllib.request
import urllib.error


class ServiceCreator:
    def __init__(self, config_path: str = 'config.json'):
        """Initialize the service creator with configuration."""
        self.config = self._load_config(config_path)
        self.api_key = self.config['api_key']
        self.alert_grouping_type = self.config['alert_grouping_type']
        self.auto_pause_enabled = self.config['auto_pause_notifications_enabled']
        self.rate_limit = self.config['rate_limit_requests_per_second']
        self.max_retries = self.config['max_retry_attempts']
        self.api_url = 'https://api.pagerduty.com/services'

        self.total_services = 0
        self.successful = 0
        self.failed_services = []

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Validate required fields
            required_fields = ['api_key', 'alert_grouping_type', 
                             'auto_pause_notifications_enabled']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field in config: {field}")

            # Validate alert_grouping_type
            if config['alert_grouping_type'] not in ['intelligent', 'time']:
                raise ValueError("alert_grouping_type must be 'intelligent' or 'time'")

            return config
        except FileNotFoundError:
            print(f"❌ Error: Config file '{config_path}' not found.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"❌ Error: Invalid JSON in config file '{config_path}'.")
            sys.exit(1)
        except ValueError as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    def _build_service_payload(self, name: str, description: str, 
                               escalation_policy_id: str) -> Dict:
        """Build the service payload for API request."""
        payload = {
            "service": {
                "type": "service",
                "name": name,
                "description": description,
                "auto_resolve_timeout": None,
                "acknowledgement_timeout": None,
                "status": "active",
                "escalation_policy": {
                    "id": escalation_policy_id,
                    "type": "escalation_policy_reference"
                },
                "incident_urgency_rule": {
                    "type": "constant",
                    "urgency": "high"
                },
                "alert_creation": "create_alerts_and_incidents",
                "alert_grouping_parameters": {
                    "type": self.alert_grouping_type
                },
                "auto_pause_notifications_parameters": {
                    "enabled": self.auto_pause_enabled,
                    "timeout": 300
                }
            }
        }

        # Add config for time-based grouping
        if self.alert_grouping_type == "time":
            payload["service"]["alert_grouping_parameters"]["config"] = {
                "timeout": 2
            }

        return payload

    def _make_request(self, payload: Dict, attempt: int = 1) -> Tuple[bool, str]:
        """Make API request to create service using urllib."""
        headers = {
            "Authorization": f"Token token={self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.pagerduty+json;version=2"
        }

        try:
            # Convert payload to JSON bytes
            data = json.dumps(payload).encode('utf-8')

            # Create request
            req = urllib.request.Request(
                self.api_url,
                data=data,
                headers=headers,
                method='POST'
            )

            # Make request
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 201:
                    return True, "Success"
                else:
                    return False, f"{response.status} {response.reason}"

        except urllib.error.HTTPError as e:
            error_msg = f"{e.code} {e.reason}"
            try:
                error_body = e.read().decode('utf-8')
                error_data = json.loads(error_body)
                if 'error' in error_data:
                    error_msg += f" - {error_data['error'].get('message', '')}"
            except:
                pass
            return False, error_msg

        except urllib.error.URLError as e:
            return False, f"Connection error: {str(e.reason)}"

        except TimeoutError:
            return False, "Request timeout"

        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def _create_service_with_retry(self, name: str, description: str, 
                                   escalation_policy_id: str, 
                                   index: int) -> Tuple[bool, str]:
        """Create a service with retry logic."""
        payload = self._build_service_payload(name, description, escalation_policy_id)

        for attempt in range(1, self.max_retries + 1):
            if attempt > 1:
                retry_msg = f"[{index}/{self.total_services}] ⚠️  Retrying: \"{name}\" (Attempt {attempt}/{self.max_retries})"
                print(retry_msg)
                time.sleep(2)  # Wait before retry

            success, message = self._make_request(payload, attempt)

            if success:
                return True, message

            # Don't retry on client errors (4xx except 429)
            if message.startswith('4') and not message.startswith('429'):
                return False, message

        return False, message

    def load_services_from_csv(self, csv_path: str = 'services.csv') -> List[Dict]:
        """Load services from CSV file."""
        services = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Validate headers
                required_columns = ['name', 'description', 'escalation_policy_id']
                if not all(col in reader.fieldnames for col in required_columns):
                    print(f"❌ Error: CSV must contain columns: {', '.join(required_columns)}")
                    sys.exit(1)

                for row in reader:
                    services.append({
                        'name': row['name'].strip(),
                        'description': row['description'].strip(),
                        'escalation_policy_id': row['escalation_policy_id'].strip()
                    })

            return services
        except FileNotFoundError:
            print(f"❌ Error: CSV file '{csv_path}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error reading CSV: {e}")
            sys.exit(1)

    def create_services(self, services: List[Dict]):
        """Create all services with progress tracking."""
        self.total_services = len(services)

        if self.total_services == 0:
            print("⚠️  No services found in CSV file.")
            return

        print(f"\n🚀 Starting bulk service creation...")
        print(f"📊 Total services to create: {self.total_services}")
        print(f"⚙️  Alert grouping type: {self.alert_grouping_type}")
        print(f"⚙️  Auto-pause notifications: {self.auto_pause_enabled}")
        print(f"⚙️  Rate limit: {self.rate_limit} requests/second")
        print(f"⚙️  Max retry attempts: {self.max_retries}")
        print(f"\n{'='*60}\n")

        for i, service in enumerate(services, 1):
            name = service['name']
            description = service['description']
            escalation_policy_id = service['escalation_policy_id']

            success, message = self._create_service_with_retry(
                name, description, escalation_policy_id, i
            )

            if success:
                success_msg = f"[{i}/{self.total_services}] ✅ Created: \"{name}\""
                print(success_msg)
                self.successful += 1
            else:
                fail_msg = f"[{i}/{self.total_services}] ❌ Failed: \"{name}\" - {message}"
                print(fail_msg)
                self.failed_services.append({
                    'name': name,
                    'description': description,
                    'escalation_policy_id': escalation_policy_id,
                    'error': message
                })

            # Rate limiting
            if i < self.total_services:
                time.sleep(1.0 / self.rate_limit)

    def save_failed_services(self, output_path: str = 'failed_services.csv'):
        """Save failed services to CSV file."""
        if not self.failed_services:
            return

        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['name', 'description', 'escalation_policy_id', 'error']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.failed_services)
            print(f"\n📄 Failed services saved to: {output_path}")
        except Exception as e:
            print(f"\n⚠️  Warning: Could not save failed services file: {e}")

    def print_summary(self):
        """Print execution summary."""
        print(f"\n{'='*60}")
        print("BULK SERVICE CREATION COMPLETE")
        print(f"{'='*60}")
        print(f"Total Services: {self.total_services}")
        print(f"✅ Successfully Created: {self.successful}")
        print(f"❌ Failed: {len(self.failed_services)}")
        print(f"{'='*60}")

        if self.failed_services:
            print(f"\nFAILED SERVICES:")
            print(f"{'-'*60}")
            for i, service in enumerate(self.failed_services, 1):
                print(f"{i}. \"{service['name']}\"")
                print(f"   Error: {service['error']}\n")
            print(f"{'-'*60}")


def main():
    """Main execution function."""
    print("\n" + "="*60)
    print("PagerDuty Bulk Service Creator")
    print("="*60)

    # Initialize creator
    creator = ServiceCreator()

    # Load services from CSV
    services = creator.load_services_from_csv()

    # Create services
    creator.create_services(services)

    # Save failed services if any
    if creator.failed_services:
        creator.save_failed_services()

    # Print summary
    creator.print_summary()

    print("\n✨ Done!\n")


if __name__ == "__main__":
    main()
