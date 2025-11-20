#!/usr/bin/env python3
"""
Log Analysis Script for ImperioCasino (Month 2).

This script analyzes structured JSON logs produced by structlog
and generates insights about application behavior.

Usage:
    python scripts/analyze_logs.py logs/app.log
    python scripts/analyze_logs.py logs/app.log --since="2025-11-20"
    python scripts/analyze_logs.py logs/app.log --errors-only
"""

import json
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import sys


def parse_log_line(line):
    """
    Parse a JSON log line.

    Args:
        line: JSON log line string

    Returns:
        dict: Parsed log entry or None if invalid
    """
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def analyze_logs(log_file, since=None, errors_only=False):
    """
    Analyze log file and generate statistics.

    Args:
        log_file: Path to log file
        since: Only analyze logs since this datetime
        errors_only: Only analyze error logs

    Returns:
        dict: Analysis results
    """
    entries = []

    with open(log_file, 'r') as f:
        for line in f:
            entry = parse_log_line(line)
            if entry:
                # Filter by date if specified
                if since:
                    try:
                        log_time = datetime.fromisoformat(entry.get('timestamp', ''))
                        if log_time < since:
                            continue
                    except:
                        pass

                # Filter by level if errors_only
                if errors_only and entry.get('level') not in ['error', 'critical']:
                    continue

                entries.append(entry)

    if not entries:
        return {'error': 'No log entries found'}

    # Analysis
    results = {
        'total_entries': len(entries),
        'time_range': {
            'start': entries[0].get('timestamp'),
            'end': entries[-1].get('timestamp')
        }
    }

    # Event types
    event_types = Counter(e.get('event') for e in entries if 'event' in e)
    results['top_events'] = event_types.most_common(10)

    # Log levels
    log_levels = Counter(e.get('level') for e in entries)
    results['log_levels'] = dict(log_levels)

    # HTTP methods and status codes
    methods = Counter(e.get('method') for e in entries if 'method' in e)
    status_codes = Counter(e.get('status_code') for e in entries if 'status_code' in e)
    results['http_methods'] = dict(methods)
    results['status_codes'] = dict(status_codes)

    # Error analysis
    errors = [e for e in entries if e.get('level') in ['error', 'critical']]
    error_types = Counter(e.get('error_type') for e in errors if 'error_type' in e)
    results['errors'] = {
        'count': len(errors),
        'types': dict(error_types.most_common(10))
    }

    # User activity
    user_actions = [e for e in entries if e.get('event') == 'user_action']
    action_types = Counter(e.get('action') for e in user_actions)
    results['user_activity'] = {
        'total_actions': len(user_actions),
        'actions': dict(action_types.most_common(10))
    }

    # Request performance
    requests = [e for e in entries if 'duration_ms' in e]
    if requests:
        durations = [e['duration_ms'] for e in requests]
        results['performance'] = {
            'total_requests': len(requests),
            'avg_duration_ms': round(sum(durations) / len(durations), 2),
            'min_duration_ms': min(durations),
            'max_duration_ms': max(durations),
            'slow_requests': len([d for d in durations if d > 1000])  # > 1 second
        }

    # Top paths
    paths = Counter(e.get('path') for e in entries if 'path' in e)
    results['top_paths'] = paths.most_common(10)

    # Unique users
    user_ids = set(e.get('user_id') for e in entries if 'user_id' in e and e.get('user_id'))
    results['unique_users'] = len(user_ids)

    # Security events
    security_events = [e for e in entries if 'security_event' in e.get('event', '')]
    results['security'] = {
        'total_events': len(security_events),
        'events': [e for e in security_events[:10]]  # Show first 10
    }

    return results


def print_analysis(results):
    """
    Print analysis results in a human-readable format.

    Args:
        results: Analysis results dictionary
    """
    print("\n" + "="*80)
    print(" ImperioCasino Log Analysis Report")
    print("="*80 + "\n")

    if 'error' in results:
        print(f"Error: {results['error']}")
        return

    print(f"Total Entries: {results['total_entries']}")
    print(f"Time Range: {results['time_range']['start']} to {results['time_range']['end']}")
    print(f"Unique Users: {results.get('unique_users', 'N/A')}\n")

    # Log Levels
    print("-" * 80)
    print("LOG LEVELS")
    print("-" * 80)
    for level, count in sorted(results['log_levels'].items()):
        print(f"  {level.upper()}: {count}")

    # Top Events
    if results.get('top_events'):
        print("\n" + "-" * 80)
        print("TOP EVENTS")
        print("-" * 80)
        for event, count in results['top_events']:
            print(f"  {event}: {count}")

    # HTTP Activity
    if results.get('http_methods'):
        print("\n" + "-" * 80)
        print("HTTP ACTIVITY")
        print("-" * 80)
        for method, count in sorted(results['http_methods'].items()):
            print(f"  {method}: {count}")

    if results.get('status_codes'):
        print("\nStatus Codes:")
        for code, count in sorted(results['status_codes'].items()):
            print(f"  {code}: {count}")

    # Performance
    if results.get('performance'):
        perf = results['performance']
        print("\n" + "-" * 80)
        print("PERFORMANCE")
        print("-" * 80)
        print(f"  Total Requests: {perf['total_requests']}")
        print(f"  Avg Duration: {perf['avg_duration_ms']}ms")
        print(f"  Min Duration: {perf['min_duration_ms']}ms")
        print(f"  Max Duration: {perf['max_duration_ms']}ms")
        print(f"  Slow Requests (>1s): {perf['slow_requests']}")

    # Errors
    if results['errors']['count'] > 0:
        print("\n" + "-" * 80)
        print("ERRORS")
        print("-" * 80)
        print(f"  Total Errors: {results['errors']['count']}")
        if results['errors']['types']:
            print("\n  Top Error Types:")
            for error_type, count in results['errors']['types'].items():
                print(f"    {error_type}: {count}")

    # User Activity
    if results.get('user_activity', {}).get('total_actions', 0) > 0:
        print("\n" + "-" * 80)
        print("USER ACTIVITY")
        print("-" * 80)
        print(f"  Total Actions: {results['user_activity']['total_actions']}")
        if results['user_activity']['actions']:
            print("\n  Top Actions:")
            for action, count in results['user_activity']['actions'].items():
                print(f"    {action}: {count}")

    # Top Paths
    if results.get('top_paths'):
        print("\n" + "-" * 80)
        print("TOP PATHS")
        print("-" * 80)
        for path, count in results['top_paths']:
            print(f"  {path}: {count}")

    # Security Events
    if results['security']['total_events'] > 0:
        print("\n" + "-" * 80)
        print("SECURITY EVENTS")
        print("-" * 80)
        print(f"  Total Events: {results['security']['total_events']}")

    print("\n" + "="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Analyze ImperioCasino structured logs')
    parser.add_argument('log_file', help='Path to log file')
    parser.add_argument('--since', help='Only analyze logs since this date (ISO format: 2025-11-20)')
    parser.add_argument('--errors-only', action='store_true', help='Only analyze error logs')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')

    args = parser.parse_args()

    # Parse since date
    since = None
    if args.since:
        try:
            since = datetime.fromisoformat(args.since)
        except ValueError:
            print(f"Invalid date format: {args.since}. Use ISO format (2025-11-20)")
            sys.exit(1)

    # Analyze logs
    try:
        results = analyze_logs(args.log_file, since=since, errors_only=args.errors_only)

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print_analysis(results)

    except FileNotFoundError:
        print(f"Error: Log file not found: {args.log_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error analyzing logs: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
