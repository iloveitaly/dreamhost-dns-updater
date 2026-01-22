#!/usr/bin/env python3

"""
This is a python script for updating the DNS Custom Records in Dreamhost Nameservers
using Dreamhost API commands.

Provided under the MIT License (MIT). See LICENSE for details.
"""

import os
import sys
import uuid
import urllib.request
import urllib.error
from typing import List, Optional, Literal
from dataclasses import dataclass

import structlog
from structlog_config import configure_logger

# Configure structured logging
configure_logger()
logger = structlog.get_logger()

# Constants
API_URL = "https://api.dreamhost.com"
Protocol = Literal["ip", "ipv6"]


@dataclass
class DNSRecord:
    account_id: str
    zone: str
    record: str
    type: str
    value: str
    comment: str
    editable: str


class DreamHostDNSUpdater:
    def __init__(self) -> None:
        self.api_key: str = os.getenv("DREAMHOST_API_KEY", "")
        self.domain: str = os.getenv("DREAMHOST_UPDATE_DOMAIN", "")
        # Set this to True to update IPv6 record.
        self.check_ipv6: bool = os.getenv("CHECK_IPV6", "0").lower() in ("1", "true", "yes")
        
        if not self.api_key or not self.domain:
            logger.error("missing_configuration", msg="API_Key and/or domain empty.")
            sys.exit(1)

        self.log = logger.bind(domain=self.domain)

    def _generate_uuid(self) -> str:
        return str(uuid.uuid4())

    def _make_url_string(self, command: str) -> str:
        return f"/?key={self.api_key}&cmd={command}&unique_id={self._generate_uuid()}"

    def _call_api(self, command: str) -> str:
        self.log.debug("api_request", command=command)
        url_suffix = self._make_url_string(command)
        full_url = API_URL + url_suffix
        
        try:
            with urllib.request.urlopen(full_url) as response:
                body = response.read().decode("UTF-8")
                self.log.debug("api_response", body=body)
                return body
        except urllib.error.URLError as e:
            self.log.error("api_connection_error", error=str(e))
            raise

    def get_dns_records(self) -> List[str]:
        response = self._call_api("dns-list_records")
        relevant_records: List[str] = []
        for line in response.splitlines():
            # Dreamhost returns records in a specific format, we filter by domain
            if self.domain in line:
                relevant_records.append(line)
        
        self.log.debug("fetched_records", count=len(relevant_records), records=relevant_records)
        return relevant_records

    def get_dns_ip(self, records: List[str], protocol: Protocol = "ip") -> Optional[str]:
        rec_type = "AAAA" if protocol == "ipv6" else "A"
        
        for line in records:
            # Format: account_id zone record type value comment editable
            # We split by tabs/spaces. The original script used .expandtabs().split()
            values = line.expandtabs().split()
            # Safety check for line length
            if len(values) < 5:
                continue
                
            record_domain = values[2]
            record_type = values[3]
            record_value = values[4]

            if record_domain == self.domain and record_type == rec_type:
                self.log.info("current_dns_record_found", protocol=protocol, value=record_value)
                return record_value
        
        self.log.warning("no_record_found", protocol=protocol)
        return None

    def del_dns_record(self, record_value: str, protocol: Protocol = "ip") -> None:
        rec_type = "AAAA" if protocol == "ipv6" else "A"
        self.log.info("deleting_record", protocol=protocol, value=record_value, type=rec_type)
        
        command = f"dns-remove_record&record={self.domain}&type={rec_type}&value={record_value}"
        response = self._call_api(command)
        
        if "error" in response:
            self.log.error("delete_record_failed", response=response)
        else:
            self.log.info("delete_record_success", response=response)

    def add_dns_record(self, address: str, protocol: Protocol = "ip") -> None:
        rec_type = "AAAA" if protocol == "ipv6" else "A"
        self.log.info("adding_record", protocol=protocol, value=address, type=rec_type)
        
        command = f"dns-add_record&record={self.domain}&type={rec_type}&value={address}"
        response = self._call_api(command)
        
        if "error" in response:
            self.log.error("add_record_failed", response=response)
        else:
            self.log.info("add_record_success", response=response)

    def update_dns_record(self, current_dns_val: Optional[str], new_address: str, protocol: Protocol = "ip") -> None:
        if current_dns_val:
            self.del_dns_record(current_dns_val, protocol)
        
        self.add_dns_record(new_address, protocol)

    def get_host_ip_address(self, protocol: Protocol = "ip") -> str:
        url = "https://api6.ipify.org" if protocol == "ipv6" else "https://checkip.amazonaws.com"
        try:
            with urllib.request.urlopen(url) as response:
                ip_addr = response.read().decode("UTF-8").strip()
                return ip_addr
        except urllib.error.URLError as e:
            self.log.error("ip_check_failed", protocol=protocol, url=url, error=str(e))
            raise

    def run(self) -> None:
        self.log.info("starting_update_process")
        
        try:
            # Get current records from DreamHost
            current_records = self.get_dns_records()
            
            # 1. Handle IPv4
            dns_ip = self.get_dns_ip(current_records, "ip")
            host_ip = self.get_host_ip_address("ip")
            
            self.log.info("ip_check", dns_ip=dns_ip, host_ip=host_ip)
            
            if dns_ip != host_ip:
                self.log.info("ip_mismatch_updating", type="A")
                self.update_dns_record(dns_ip, host_ip, "ip")
            else:
                self.log.info("ip_up_to_date", type="A")

            # 2. Handle IPv6 if enabled
            if self.check_ipv6:
                dns_ipv6 = self.get_dns_ip(current_records, "ipv6")
                host_ipv6 = self.get_host_ip_address("ipv6")
                
                self.log.info("ipv6_check", dns_ip=dns_ipv6, host_ip=host_ipv6)
                
                if dns_ipv6 != host_ipv6:
                    self.log.info("ip_mismatch_updating", type="AAAA")
                    self.update_dns_record(dns_ipv6, host_ipv6, "ipv6")
                else:
                    self.log.info("ip_up_to_date", type="AAAA")

        except Exception as e:
            self.log.exception("unhandled_exception", error=str(e))
            sys.exit(1)


if __name__ == "__main__":
    updater = DreamHostDNSUpdater()
    updater.run()