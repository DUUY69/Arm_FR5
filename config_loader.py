#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config Loader - Đọc cấu hình từ config.env
"""

import os


class ConfigLoader:
    """Load configuration từ file env"""
    
    def __init__(self):
        self.config = {}
        # Load config từ IOTController_Python/config.env
        iot_config_file = os.path.join('IOTController_Python', 'config.env')
        if os.path.exists(iot_config_file):
            self.load_iot_config(iot_config_file)
        
        # Thêm config mặc định cho workflow
        self.config.setdefault('WORKFLOW_FOLDER', 'workflows')
        self.config.setdefault('WORKFLOW_ROBOT_IP', '192.168.58.2')
        self.config.setdefault('DEFAULT_TIMEOUT', 5.0)
        self.config.setdefault('DEFAULT_RETRY_COUNT', 1)
    
    def load_config(self, env_file):
        """Load configuration từ file"""
        if not os.path.exists(env_file):
            print(f"⚠️ File config không tìm thấy: {env_file}")
            return
        
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Bỏ qua comment và dòng trống
                if not line or line.startswith('#'):
                    continue
                
                # Parse key=value
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Xử lý boolean
                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    # Xử lý số
                    elif value.isdigit():
                        value = int(value)
                    elif self._is_float(value):
                        value = float(value)
                    
                    self.config[key] = value
    
    def load_iot_config(self, iot_config_file):
        """Load IoT config từ IOTController_Python/config.env"""
        with open(iot_config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Bỏ qua comment và dòng trống
                if not line or line.startswith('#'):
                    continue
                
                # Parse DEVICE_NAME=COM_PORT,BAUDRATE
                if '=' in line:
                    key, value = line.split('=', 1)
                    device_name = key.strip()
                    # Parse COM_PORT,BAUDRATE
                    if ',' in value:
                        parts = value.strip().split(',')
                        port = parts[0].strip()
                        baudrate = int(parts[1].strip()) if len(parts) > 1 else 115200
                        
                        # Convert sang format mới: DEVICE_PORT, DEVICE_BAUDRATE, DEVICE_NAME
                        self.config[f'{device_name}_PORT'] = port
                        self.config[f'{device_name}_BAUDRATE'] = baudrate
                        self.config[f'{device_name}_NAME'] = device_name
    
    def _is_float(self, value):
        """Check if value is float"""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def get(self, key, default=None):
        """Get config value"""
        return self.config.get(key, default)
    
    def get_device_config(self, device_name):
        """Get device configuration"""
        return {
            'port': self.get(f'{device_name}_PORT'),
            'baudrate': self.get(f'{device_name}_BAUDRATE', 115200),
            'name': self.get(f'{device_name}_NAME', device_name)
        }


# Singleton instance
_config_loader = None

def get_config():
    """Get global config loader instance"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


# Convenience functions
def get_iot_device_config(device_name):
    """Get IoT device config"""
    config = get_config()
    return config.get_device_config(device_name)


def get_robot_ip():
    """Get robot IP"""
    return get_config().get('WORKFLOW_ROBOT_IP', '192.168.58.2')


def get_workflow_folder():
    """Get workflow folder path"""
    folder = get_config().get('WORKFLOW_FOLDER', 'workflows')
    return folder


def get_default_timeout():
    """Get default timeout"""
    return get_config().get('DEFAULT_TIMEOUT', 5.0)


def get_default_retry_count():
    """Get default retry count"""
    return get_config().get('DEFAULT_RETRY_COUNT', 1)


if __name__ == "__main__":
    # Test config loader
    config = ConfigLoader()
    print("📋 Config loaded:")
    print(f"Robot IP: {config.get('ROBOT_IP')}")
    print(f"Workflow folder: {config.get('WORKFLOW_FOLDER')}")
    print()
    print("Devices:")
    for device in ['STIRRER', 'COFFEE_MAKER', 'ICE_MAKER']:
        device_config = config.get_device_config(device)
        print(f"  {device}: {device_config}")

