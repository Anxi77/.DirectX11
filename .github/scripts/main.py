#!/usr/bin/env python3
"""Simplified GitHub automation system - Core functionality only."""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add automation directory to Python path before domain imports
automation_dir = Path(__file__).parent
sys.path.insert(0, str(automation_dir))

# Import domain modules after path setup (to avoid E402 in this specific case)
from infrastructure.config_manager import ConfigurationManager  # noqa: E402
from infrastructure.api_client import APIClient  # noqa: E402
from domains.commits import CommitParser  # noqa: E402
from domains.reporting import DailyReporter  # noqa: E402
from domains.projects import BoardSync, run_todo_sync  # noqa: E402
from domains.issues import TodoIssueManager  # noqa: E402


class GitHubAutomation:
    """Simplified GitHub automation system - Core functionality only."""

    def __init__(self, config_path: Optional[str] = None, dry_run: bool = False):
        """Initialize automation system.

        Args:
            config_path: Path to configuration file
            dry_run: If True, don't make actual changes
        """
        self.dry_run = dry_run

        # Initialize configuration manager with environment support
        self.config_manager = ConfigurationManager(config_path)
        environment = os.environ.get('AUTOMATION_ENV', 'production')
        self.config = self.config_manager.load_config(environment)

        self._setup_logging()

        self.logger = logging.getLogger(__name__)
        self.api_client = None

        # Core components
        self.commit_parser = CommitParser()
        self.daily_reporter = None
        self.board_sync = None

    def _setup_logging(self):
        """Setup logging configuration."""
        log_config = self.config.get('logging', {})

        log_level = getattr(logging, log_config.get('level', 'INFO').upper())
        log_format = log_config.get('format', '%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        date_format = log_config.get('date_format', '%Y-%m-%d %H:%M:%S')

        logging.basicConfig(
            level=log_level,
            format=log_format,
            datefmt=date_format
        )

        # Set component-specific log levels
        loggers = log_config.get('loggers', {})
        for logger_name, level in loggers.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(getattr(logging, level.upper()))

    def initialize(self) -> bool:
        """Initialize the automation system."""
        try:
            # Validate required environment variables
            required_vars = ['GITHUB_TOKEN', 'GITHUB_REPOSITORY']
            missing_vars = [var for var in required_vars if not os.environ.get(var)]
            if missing_vars:
                self.logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
                return False

            # Get GitHub token with PAT priority
            pat_token = os.environ.get('PAT')
            github_token = os.environ.get('GITHUB_TOKEN')
            
            # Determine which token to use and log it
            if pat_token:
                actual_token = pat_token
                token_type = "PAT (Personal Access Token)"
                self.logger.info(f"🔑 Using PAT token (starts with: {pat_token[:8]}...)")
            elif github_token:
                actual_token = github_token
                token_type = "GITHUB_TOKEN (Actions default)"
                self.logger.info(f"🔑 Using GITHUB_TOKEN (starts with: {github_token[:8]}...)")
            else:
                self.logger.error("❌ No GitHub token found (neither PAT nor GITHUB_TOKEN)")
                return False

            # Initialize GitHub client
            github_config = self.config.get('github', {})
            self.api_client = APIClient(
                token=actual_token,
                max_retries=github_config.get('max_retries', 3),
                base_delay=github_config.get('base_delay', 1.0)
            )
            
            self.logger.info(f"📡 GitHub API client initialized with {token_type}")
            
            # Test API access
            try:
                rate_limit = self.api_client.get_rate_limit()
                remaining = rate_limit.get('remaining', 'unknown')
                self.logger.info(f"✅ API connection successful - Rate limit remaining: {remaining}")
            except Exception as e:
                self.logger.warning(f"⚠️ API connection test failed: {e}")

            # Get repository info
            repo_name = os.environ.get('GITHUB_REPOSITORY')
            if not repo_name:
                self.logger.error("GITHUB_REPOSITORY not found in environment")
                return False

            self.repo_name = repo_name
            self.logger.info(f"Connected to repository: {repo_name}")

            # Initialize core components
            if self.config.get('daily_reporter', {}).get('enabled', True):
                self.daily_reporter = DailyReporter(
                    self.api_client,
                    self.config.get('daily_reporter', {})
                )

            if self.config.get('board_sync', {}).get('enabled', True):
                # Split repository name into owner and repo parts
                repo_owner, repo_name_only = self.repo_name.split('/', 1)
                self.board_sync = BoardSync(
                    self.api_client,
                    self.config.get('board_sync', {}),
                    repo_owner,
                    repo_name_only
                )

            self.logger.info("GitHub automation system initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize automation system: {e}")
            return False

    def _should_skip_automation(self) -> bool:
        """Check if automation should be skipped based on actor and conditions."""
        actor = os.environ.get('GITHUB_ACTOR', '')
        excluded_actors = ['github-actions[bot]', 'dependabot[bot]', 'renovate[bot]']

        if actor in excluded_actors:
            self.logger.info(f"Skipping - automated actor: {actor}")
            return True

        # Check commit message if available
        commit_sha = os.environ.get('GITHUB_SHA')
        if commit_sha:
            try:
                repo_owner, repo_name = self.repo_name.split('/', 1)
                commit = self.api_client.get_commit(repo_owner, repo_name, commit_sha)
                message = commit.get('message', '').lower()

                skip_patterns = ['[skip-automation]']
                if any(pattern in message for pattern in skip_patterns):
                    self.logger.info(f"Skipping - commit contains skip pattern: {skip_patterns}")
                    return True

            except Exception as e:
                self.logger.warning(f"Failed to check commit message: {e}")
                # Continue processing even if commit check fails

        return False

    def run_workflow_tracking(self) -> Dict[str, Any]:
        """Run workflow tracking (commit-based DSR generation)."""
        if not self.daily_reporter:
            return {'error': 'Daily reporter not initialized'}

        try:
            self.logger.info("Starting workflow tracking")

            if self._should_skip_automation():
                return {'skipped': True, 'reason': 'automation_bypass'}

            # Generate DSR
            if self.dry_run:
                self.logger.info("DRY RUN: Would generate DSR issue")
                return {'success': True, 'dry_run': True}

            # Generate DSR using GraphQL API
            repo_owner, repo_name = self.repo_name.split('/', 1)
            dsr_issue = self.daily_reporter.generate_dsr(repo_owner, repo_name)

            if dsr_issue:
                # After DSR generation, sync TODO issues to project board
                self.logger.info("Running TODO project synchronization...")
                try:
                    todo_sync_success = run_todo_sync(self.api_client, self.config, repo_owner, repo_name)
                    if todo_sync_success:
                        self.logger.info("✅ TODO project sync completed successfully")
                    else:
                        self.logger.warning("⚠️ TODO project sync completed with issues")
                except Exception as e:
                    self.logger.error(f"TODO project sync failed: {e}")

                return {
                    'success': True,
                    'dsr_issue': {
                        'number': dsr_issue.get('number'),
                        'title': dsr_issue.get('title'),
                        'url': dsr_issue.get('url')
                    },
                    'todo_sync': todo_sync_success if 'todo_sync_success' in locals() else False
                }
            else:
                return {'success': False, 'reason': 'no_commits_today'}

        except Exception as e:
            self.logger.error(f"Workflow tracking failed: {e}")
            return {'error': str(e)}

    def run_task_management(self) -> Dict[str, Any]:
        """Run task management (issue/project sync)."""
        if not self.board_sync:
            return {'error': 'Project sync not initialized'}

        try:
            self.logger.info("Starting task management")

            if self._should_skip_automation():
                return {'skipped': True, 'reason': 'automation_bypass'}

            if self.dry_run:
                self.logger.info("DRY RUN: Would sync project board")
                return {'success': True, 'dry_run': True}

            # Sync project board (uses repository details from BoardSync initialization)
            sync_results = self.board_sync.sync_board()

            return {
                'success': True,
                'board_sync': sync_results
            }

        except Exception as e:
            self.logger.error(f"Task management failed: {e}")
            return {'error': str(e)}

    def run_project_report(self) -> Dict[str, Any]:
        """Generate project status report."""
        try:
            self.logger.info("Generating project report")

            if self.dry_run:
                self.logger.info("DRY RUN: Would generate project report")
                return {'success': True, 'dry_run': True}

            # Generate comprehensive project report
            repo_name = os.environ.get('GITHUB_REPOSITORY')
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'repository': repo_name
            }

            # Add daily reporter stats
            if self.daily_reporter:
                dsr_stats = self.daily_reporter.get_statistics()
                report_data['dsr_statistics'] = dsr_stats

            # Add project sync stats
            if self.board_sync and repo_name:
                repo_owner, repo_name_only = repo_name.split('/', 1)
                sync_stats = self.board_sync.get_project_statistics(repo_owner, repo_name_only)
                report_data['project_statistics'] = sync_stats

            return {
                'success': True,
                'report': report_data
            }

        except Exception as e:
            self.logger.error(f"Project report failed: {e}")
            return {'error': str(e)}

    def run_dsr_sync(self) -> Dict[str, Any]:
        """Synchronize DSR checkboxes with linked issue states."""
        try:
            self.logger.info("Starting DSR synchronization")

            if self.dry_run:
                self.logger.info("Dry run mode - no actual synchronization")
                return {'success': True, 'dry_run': True}

            repo_name = os.environ.get('GITHUB_REPOSITORY')
            if not repo_name:
                self.logger.error("GITHUB_REPOSITORY environment variable not set")
                return {'error': 'Repository not specified'}

            repo_owner, repo_name_only = repo_name.split('/', 1)

            # Initialize TODO issue manager
            todo_manager = TodoIssueManager(self.api_client, self.config.get('todo_issues', {}))

            # Find all open DSR issues
            dsr_label = self.config.get('daily_reporter', {}).get('dsr_label', 'DSR')
            issues = self.api_client.get_issues(
                repo_owner,
                repo_name_only,
                state='OPEN',
                labels=[dsr_label]
            )
            
            self.logger.info(f"🔍 Found {len(issues)} open DSR issues with label '{dsr_label}'")

            sync_results = {
                'synced_issues': [],
                'errors': []
            }

            for issue in issues:
                try:
                    issue_id = issue.get('id')
                    issue_number = issue.get('number')
                    issue_body = issue.get('body', '')

                    if not issue_id:
                        continue

                    # Extract issue links from DSR body
                    issue_links = self._extract_issue_links_from_dsr(issue_body)

                    if not issue_links:
                        self.logger.info(f"📭 No linked issues found in DSR #{issue_number}")
                        self.logger.debug(f"DSR body preview: {issue_body[:200]}...")
                        continue
                    
                    self.logger.info(f"📋 Found {len(issue_links)} linked issues in DSR #{issue_number}: {list(issue_links.values())}")

                    # Synchronize checkboxes with issue states
                    success = todo_manager.sync_dsr_checkboxes(issue_id, issue_links)

                    if success:
                        sync_results['synced_issues'].append({
                            'dsr_number': issue_number,
                            'linked_issues': list(issue_links.values()),
                            'status': 'synced'
                        })
                        self.logger.info(f"Synchronized DSR #{issue_number} with {len(issue_links)} linked issues")
                    else:
                        sync_results['errors'].append({
                            'dsr_number': issue_number,
                            'error': 'Sync failed'
                        })

                except Exception as e:
                    self.logger.error(f"Failed to sync DSR #{issue.get('number', 'unknown')}: {e}")
                    sync_results['errors'].append({
                        'dsr_number': issue.get('number', 'unknown'),
                        'error': str(e)
                    })

            self.logger.info(
                f"DSR sync completed: {len(sync_results['synced_issues'])} synced, "
                f"{len(sync_results['errors'])} errors"
            )

            return {
                'success': True,
                'results': sync_results
            }

        except Exception as e:
            self.logger.error(f"DSR sync failed: {e}")
            return {'error': str(e)}

    def _extract_issue_links_from_dsr(self, dsr_body: str) -> Dict[str, int]:
        """Extract issue links from DSR body.

        Args:
            dsr_body: DSR issue body content

        Returns:
            Dictionary mapping task descriptions to issue numbers
        """
        import re
        issue_links = {}

        if not dsr_body:
            return issue_links

        # Find all checkbox lines with issue references
        lines = dsr_body.split('\n')
        for line in lines:
            line = line.strip()

            # Look for both formats:
            # New format: "- [] #123" or "- [x] #123" 
            # Old format: "- [ ] Task description (#123)"
            
            if line.startswith('- ['):
                # New format: "- [] #123" or "- [x] #123"
                new_format_match = re.match(r'^- \[(x?)\] #(\d+)', line)
                if new_format_match:
                    issue_number = int(new_format_match.group(2))
                    # Use issue number as key since we don't have task description
                    task_key = f"issue_{issue_number}"
                    issue_links[task_key] = issue_number
                    continue
                
                # Old format: "- [ ] Task description (#123)"
                elif '(#' in line:
                    issue_match = re.search(r'\(#(\d+)\)', line)
                    if issue_match:
                        issue_number = int(issue_match.group(1))

                        # Extract task description (remove checkbox and issue reference)
                        task = line[6:].strip()  # Remove "- [ ] " or "- [x] "
                        task = re.sub(r'\s*\(#\d+\)\s*$', '', task).strip()

                        if task:
                            issue_links[task] = issue_number

        return issue_links

    def health_check(self) -> Dict[str, Any]:
        """Perform system health check."""
        health = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }

        try:
            # Check GitHub client
            if self.api_client:
                rate_limit = self.api_client.get_rate_limit()
                health['components']['api_client'] = {
                    'status': 'healthy',
                    'rate_limit_remaining': rate_limit.get('remaining', 0),
                    'rate_limit_limit': rate_limit.get('limit', 0)
                }
            else:
                health['components']['api_client'] = {'status': 'not_initialized'}

            # Check repository access
            if hasattr(self, 'repo_name') and self.repo_name:
                health['components']['repository'] = {
                    'status': 'healthy',
                    'name': self.repo_name,
                    'configured': True
                }
            else:
                health['components']['repository'] = {'status': 'not_initialized'}

            # Check core components
            health['components']['daily_reporter'] = {
                'status': 'enabled' if self.daily_reporter else 'disabled'
            }
            health['components']['board_sync'] = {
                'status': 'enabled' if self.board_sync else 'disabled'
            }

            return health

        except Exception as e:
            health['overall_status'] = 'unhealthy'
            health['error'] = str(e)
            return health

def create_argument_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description='GitHub Automation System - Core functionality',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --mode workflow          # Process commits and generate DSR
  python main.py --mode task-management   # Sync project board
  python main.py --mode report            # Generate project report
  python main.py --mode sync-dsr          # Sync DSR checkboxes with linked issues
  python main.py --health-check           # Check system health
  python main.py --dry-run --verbose      # Test without changes
        """
    )

    parser.add_argument(
        '--mode',
        choices=['workflow', 'task-management', 'report', 'sync-dsr'],
        default='workflow',
        help='Automation mode to run'
    )

    parser.add_argument(
        '--config',
        help='Path to configuration file'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without making actual changes'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--health-check',
        action='store_true',
        help='Perform system health check'
    )

    return parser


def main():
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Override log level if verbose
    if args.verbose:
        os.environ['AUTOMATION_LOG_LEVEL'] = 'DEBUG'

    # Initialize automation system
    automation = GitHubAutomation(
        config_path=args.config,
        dry_run=args.dry_run
    )

    if not automation.initialize():
        print("❌ Failed to initialize automation system")
        sys.exit(1)

    # Run health check if requested
    if args.health_check:
        health = automation.health_check()
        print("🏥 System Health Check:")
        print(f"Overall Status: {health['overall_status'].upper()}")

        for component, status in health['components'].items():
            print(f"  {component}: {status['status'].upper()}")

        if health['overall_status'] == 'unhealthy':
            print(f"Error: {health.get('error', 'Unknown error')}")
            sys.exit(1)

        print("✅ All systems healthy")
        return

    # Run automation mode
    try:
        if args.mode == 'workflow':
            results = automation.run_workflow_tracking()
        elif args.mode == 'task-management':
            results = automation.run_task_management()
        elif args.mode == 'report':
            results = automation.run_project_report()
        elif args.mode == 'sync-dsr':
            results = automation.run_dsr_sync()
        else:
            print(f"❌ Unknown mode: {args.mode}")
            sys.exit(1)

        # Output results
        if results.get('success'):
            print("✅ Automation completed successfully")

            if args.mode == 'workflow' and 'dsr_issue' in results:
                dsr = results['dsr_issue']
                print(f"📅 DSR Issue: #{dsr['number']} - {dsr['title']}")

            elif args.mode == 'task-management' and 'board_sync' in results:
                sync = results['board_sync']
                print(f"📊 Project Sync: Updated {sync.get('updated_items', 0)} items")

            elif args.mode == 'report':
                print("📈 Project report generated")

            elif args.mode == 'sync-dsr' and 'results' in results:
                sync_data = results['results']
                synced_count = len(sync_data.get('synced_issues', []))
                error_count = len(sync_data.get('errors', []))
                print(f"🔄 DSR Sync: {synced_count} issues synced, {error_count} errors")

        elif results.get('skipped'):
            print(f"⏭️ Automation skipped: {results.get('reason', 'unknown')}")

        elif results.get('error'):
            print(f"❌ Automation failed: {results['error']}")
            sys.exit(1)

        else:
            print(f"⚠️ Unexpected result: {results}")

    except KeyboardInterrupt:
        print("\n🛑 Automation interrupted by user")
        sys.exit(130)

    except Exception as e:
        automation.logger.error(f"Unexpected error: {e}")
        print(f"💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
