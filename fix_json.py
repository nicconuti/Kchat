#!/usr/bin/env python3
"""
Standardized JSON Repair Tool
Uses industry-standard json-repair library + custom K-Array specific fixes
Handles all common JSON corruption patterns including LLM-generated malformed JSON
"""

import json
import shutil
import sys
from pathlib import Path
from typing import Tuple, List, Dict, Any
import logging

# Try to import json-repair library
try:
    from json_repair import repair_json
    JSON_REPAIR_AVAILABLE = True
    print("✅ Using json-repair library (industry standard)")
except ImportError:
    JSON_REPAIR_AVAILABLE = False
    print("⚠️  json-repair not available. Install with: pip install json-repair")

# Fallback: try fix-busted-json
try:
    from fix_busted_json import repair_json as fix_busted_repair
    FIX_BUSTED_AVAILABLE = True
    if not JSON_REPAIR_AVAILABLE:
        print("✅ Using fix-busted-json as fallback")
except ImportError:
    FIX_BUSTED_AVAILABLE = False
    if not JSON_REPAIR_AVAILABLE:
        print("⚠️  fix-busted-json not available. Install with: pip install fix-busted-json")


class JSONRepairTool:
    """Comprehensive JSON repair tool with multiple strategies"""
    
    def __init__(self, data_directory: str = "data"):
        self.data_dir = Path(data_directory)
        self.setup_logging()
        
        # Statistics
        self.stats = {
            'total_files': 0,
            'already_valid': 0,
            'repaired_json_repair': 0,
            'repaired_fix_busted': 0,
            'repaired_custom': 0,
            'failed': 0,
            'error_files': []
        }
    
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('json_repair.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_json(self, content: str) -> Tuple[bool, str]:
        """Validate JSON and return error details"""
        try:
            json.loads(content)
            return True, ""
        except json.JSONDecodeError as e:
            return False, str(e)
    
    def custom_k_array_fixes(self, content: str) -> str:
        """Custom fixes for K-Array specific patterns"""
        
        # Fix 1: Source citations with unescaped quotes
        # Pattern: (Source: "text with "quotes" inside")
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            if '(Source: "' in line and line.count('"') > 4:
                # Find Source patterns and fix them
                while '(Source: "' in line:
                    start_pos = line.find('(Source: "')
                    if start_pos == -1:
                        break
                    
                    # Find the end of the source citation
                    search_start = start_pos + len('(Source: "')
                    end_pos = line.find('")', search_start)
                    
                    if end_pos != -1:
                        # Extract source content
                        source_content = line[search_start:end_pos]
                        # Escape internal quotes
                        escaped_content = source_content.replace('"', '\\"')
                        # Replace in line
                        line = line[:search_start] + escaped_content + line[end_pos:]
                    else:
                        break
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # Fix 2: Inch measurements (e.g., 12" -> 12\")
        import re
        content = re.sub(r'(\d+\.?\d*)"(?=\s|[,}\]])', r'\1\\"', content)
        
        # Fix 3: Common quote patterns in descriptions
        content = re.sub(r'(\w)"(\w)', r'\1\\"\2', content)
        
        return content
    
    def repair_with_json_repair(self, content: str) -> Tuple[bool, str]:
        """Repair using json-repair library"""
        if not JSON_REPAIR_AVAILABLE:
            return False, content
        
        try:
            repaired = repair_json(content)
            # Validate the repaired JSON
            json.loads(repaired)
            return True, repaired
        except Exception as e:
            self.logger.debug(f"json-repair failed: {e}")
            return False, content
    
    def repair_with_fix_busted(self, content: str) -> Tuple[bool, str]:
        """Repair using fix-busted-json library"""
        if not FIX_BUSTED_AVAILABLE:
            return False, content
        
        try:
            repaired = fix_busted_repair(content)
            # Validate the repaired JSON
            json.loads(repaired)
            return True, repaired
        except Exception as e:
            self.logger.debug(f"fix-busted-json failed: {e}")
            return False, content
    
    def repair_json_content(self, content: str) -> Tuple[bool, str, str]:
        """
        Comprehensive JSON repair using multiple strategies
        Returns: (success, repaired_content, method_used)
        """
        
        # Strategy 1: json-repair library (most advanced)
        success, repaired = self.repair_with_json_repair(content)
        if success:
            return True, repaired, "json-repair"
        
        # Strategy 2: fix-busted-json library
        success, repaired = self.repair_with_fix_busted(content)
        if success:
            return True, repaired, "fix-busted-json"
        
        # Strategy 3: Custom K-Array specific fixes
        try:
            custom_fixed = self.custom_k_array_fixes(content)
            
            # Try json-repair again after custom fixes
            if JSON_REPAIR_AVAILABLE:
                try:
                    final_repaired = repair_json(custom_fixed)
                    json.loads(final_repaired)
                    return True, final_repaired, "custom+json-repair"
                except:
                    pass
            
            # Validate custom fixes
            json.loads(custom_fixed)
            return True, custom_fixed, "custom"
            
        except Exception as e:
            self.logger.debug(f"Custom fixes failed: {e}")
            return False, content, "failed"
    
    def process_file(self, file_path: Path) -> bool:
        """Process a single JSON file"""
        try:
            self.logger.info(f"Processing: {file_path.name}")
            
            # Read content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if already valid
            is_valid, error = self.validate_json(content)
            if is_valid:
                self.logger.info(f"  ✅ Already valid")
                self.stats['already_valid'] += 1
                return True
            
            self.logger.info(f"  🔧 Invalid JSON: {error}")
            
            # Create backup
            backup_path = file_path.with_suffix('.json.backup')
            if not backup_path.exists():
                shutil.copy2(file_path, backup_path)
                self.logger.info(f"  📁 Backup created")
            
            # Attempt repair
            success, repaired_content, method = self.repair_json_content(content)
            
            if success:
                # Save repaired content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(repaired_content)
                
                self.logger.info(f"  ✅ Repaired using: {method}")
                
                # Update statistics
                if method.startswith('json-repair'):
                    self.stats['repaired_json_repair'] += 1
                elif method.startswith('fix-busted'):
                    self.stats['repaired_fix_busted'] += 1
                else:
                    self.stats['repaired_custom'] += 1
                
                return True
            else:
                self.logger.warning(f"  ❌ Could not repair: {file_path.name}")
                self.stats['failed'] += 1
                self.stats['error_files'].append(file_path.name)
                return False
                
        except Exception as e:
            self.logger.error(f"  ❌ Error processing {file_path.name}: {e}")
            self.stats['failed'] += 1
            self.stats['error_files'].append(file_path.name)
            return False
    
    def run(self) -> Dict[str, Any]:
        """Run the JSON repair tool on all files"""
        
        if not self.data_dir.exists():
            self.logger.error(f"❌ Directory not found: {self.data_dir}")
            return self.stats
        
        # Get all JSON files (exclude backups)
        json_files = [f for f in self.data_dir.glob("*.json") if not f.name.endswith('.backup')]
        
        if not json_files:
            self.logger.warning(f"⚠️  No JSON files found in {self.data_dir}")
            return self.stats
        
        self.stats['total_files'] = len(json_files)
        
        self.logger.info("🔧 Standardized JSON Repair Tool")
        self.logger.info("=" * 60)
        self.logger.info(f"📁 Processing {len(json_files)} files in {self.data_dir}")
        
        # Process files
        for json_file in sorted(json_files):
            self.process_file(json_file)
        
        return self.stats
    
    def print_summary(self):
        """Print summary statistics"""
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📊 REPAIR SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"📁 Total files processed: {self.stats['total_files']}")
        self.logger.info(f"✅ Already valid: {self.stats['already_valid']}")
        self.logger.info(f"🔧 Repaired with json-repair: {self.stats['repaired_json_repair']}")
        self.logger.info(f"🔧 Repaired with fix-busted-json: {self.stats['repaired_fix_busted']}")
        self.logger.info(f"🔧 Repaired with custom fixes: {self.stats['repaired_custom']}")
        self.logger.info(f"❌ Failed to repair: {self.stats['failed']}")
        
        success_rate = ((self.stats['total_files'] - self.stats['failed']) / self.stats['total_files'] * 100) if self.stats['total_files'] > 0 else 0
        self.logger.info(f"📈 Success rate: {success_rate:.1f}%")
        
        if self.stats['error_files']:
            self.logger.info(f"\n📋 Files that could not be repaired:")
            for filename in self.stats['error_files'][:10]:
                self.logger.info(f"   - {filename}")
            if len(self.stats['error_files']) > 10:
                self.logger.info(f"   ... and {len(self.stats['error_files']) - 10} more")
        
        if self.stats['failed'] == 0:
            self.logger.info(f"\n🎉 ALL JSON FILES REPAIRED SUCCESSFULLY!")
            self.logger.info(f"Ready to start the chat system:")
            self.logger.info(f"   python3 k_array_chat.py")
        else:
            self.logger.info(f"\n💡 To install missing libraries:")
            if not JSON_REPAIR_AVAILABLE:
                self.logger.info(f"   pip install json-repair")
            if not FIX_BUSTED_AVAILABLE:
                self.logger.info(f"   pip install fix-busted-json")


def main():
    """Main function"""
    
    # Check if libraries are available
    if not JSON_REPAIR_AVAILABLE and not FIX_BUSTED_AVAILABLE:
        print("❌ No JSON repair libraries available!")
        print("📦 Install at least one of:")
        print("   pip install json-repair")
        print("   pip install fix-busted-json")
        print("\nNote: json-repair is recommended (most advanced)")
        return
    
    # Create and run the repair tool
    repair_tool = JSONRepairTool()
    repair_tool.run()
    repair_tool.print_summary()


if __name__ == "__main__":
    main()