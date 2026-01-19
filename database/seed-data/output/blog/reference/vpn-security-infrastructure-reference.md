# **[Pattern] VPN & Secure Infrastructure Reference Guide**

---

## **1. Overview**

The **VPN & Secure Infrastructure** pattern establishes a robust framework for creating private, encrypted network connections between remote users, branch offices, and cloud services. This pattern leverages **Virtual Private Networks (VPNs), site-to-site VPNs, and secure infrastructure components** (e.g., firewalls, encryption gateways, and identity management) to ensure **confidentiality, integrity, and availability** of data in transit.

This guide provides **implementation best practices, architectural decisions, and automation considerations** to deploy a secure, scalable VPN infrastructure. It covers **on-premises, cloud, and hybrid environments**, with recommendations for **zero-trust architectures, network segmentation, and compliance alignment**.

---

## **2. Key Concepts & Implementation Details**

### **2.1 Core Components**
| **Component**          | **Purpose**                                                                 | **Key Considerations**                                                                 |
|------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **VPN Gateway**        | Encrypts and routes traffic between endpoints.                              | High availability, redundancy, and support for **IPsec/IKEv2, WireGuard, or OpenVPN**. |
| **Site-to-Site VPN**   | Connects remote locations (e.g., offices, data centers) securely.          | Dynamic routing (BGP), failover mechanisms, and **MTU optimization**.               |
| **Client VPN**         | Allows remote users to connect securely to an internal network.             | **Split tunneling**, user authentication (TLS, Certificate-based), and **OAuth 2.0/OIDC** integration. |
| **Firewall & NAC**     | Enforces access controls and inspects traffic.                             | **Stateful inspection**, application-level filtering, and **IP reputation blocking**. |
| **Encryption Protocols** | Ensures data privacy in transit.                                          | **AES-256, RSA-4096** for strong encryption; **Perfect Forward Secrecy (PFS)**.     |
| **Identity & Access**  | Manages authentication and authorization.                                 | **LDAP, SAML, or federation (Okta, Azure AD)**; **MFA enforcement**.                |
| **Network Segmentation** | Isolates sensitive resources for defense-in-depth.                      | **Micro-segmentation** (e.g., NSGs in Azure, Security Groups in AWS).               |
| **Logging & Monitoring** | Detects anomalies and ensures compliance.                               | **SIEM integration (Splunk, ELK), threat intelligence feeds, and audit logging (PCI DSS, GDPR, HIPAA).** |

---

### **2.2 Architectural Patterns**
#### **A. Traditional VPN (Legacy)**
- **Use Case**: On-premises-to-cloud or remote-to-office connectivity.
- **Pros**: Simple, widely supported.
- **Cons**: **Single point of failure**, lack of granular access control.
- **Implementation**:
  - Deploy **VPN gateways** (e.g., **FortiGate, Cisco ASA, Azure VPN Gateway**).
  - Use **IPSec/IKEv2** for encryption.
  - Enforce **Network Address Translation (NAT)** to hide internal IPs.

#### **B. Zero-Trust VPN (Modern)**
- **Use Case**: Cloud-first, hybrid environments with **least-privilege access**.
- **Pros**: **No-trust assumptions**, **identity-aware access**, continuous authentication.
- **Cons**: Requires **strong IAM integration**.
- **Implementation**:
  - Use **BeyondCorp (Google) or Zscaler Private Access** for **identity-based VPN**.
  - Replace **static IPs** with **dynamic VPN assignments**.
  - Enforce **just-in-time (JIT) access** via **service mesh (e.g., Istio, Linkerd)**.

#### **C. Hybrid VPN (On-Prem + Cloud)**
- **Use Case**: Gradual cloud migration with legacy dependency.
- **Pros**: **Seamless integration** between on-prem and cloud.
- **Cons**: **Complex routing**, potential **latency issues**.
- **Implementation**:
  - Deploy **VPN appliances** (e.g., **Palo Alto, Palo Alto GlobalProtect**) for hybrid tunnels.
  - Use **BGP dynamic routing** between on-prem and cloud gateways.
  - Implement **VPN split tunneling** to route sensitive traffic via VPN.

---

### **2.3 Best Practices**
| **Category**               | **Best Practice**                                                                 |
|----------------------------|-----------------------------------------------------------------------------------|
| **Encryption**             | Enforce **AES-256-GCM** for VPN tunnels; rotate keys **every 90 days**.          |
| **Authentication**         | **Certificate-based auth** (for machines) + **MFA (TOTP/FIDO2)** for users.      |
| **Network Design**         | **Isolate VPN traffic** from public internet; use **dedicated subnets**.         |
| **Performance**            | **MTU optimization** (1400-1500 bytes); **load balance VPN gateways**.             |
| **Compliance**             | **Audit logs** for all VPN connections; comply with **PCI DSS (required for payment data)**. |
| **Disaster Recovery**      | **Multi-region VPN gateways** with **failover scripts**.                         |

---

## **3. Schema Reference**

### **3.1 VPN Gateway Schema (Cloud Provider Agnostic)**
| **Field**               | **Type**       | **Description**                                                                 | **Example Values**                          |
|-------------------------|----------------|-------------------------------------------------------------------------------|---------------------------------------------|
| `gateway_name`          | String         | Unique identifier for the VPN gateway.                                         | `corp-vpn-gw-eu-west-1`                     |
| `gateway_type`          | Enum           | Type of VPN (Client, Site-to-Site, Hybrid).                                   | `"SiteToSite"`, `"Client"`                  |
| `protocol`              | Enum           | Encryption protocol used.                                                     | `"IPSecIKEv2"`, `"WireGuard"`, `"OpenVPN"`   |
| `encryption_key`        | String (Base64) | Symmetric encryption key (stored securely in **KMS/AWS Secrets Manager**).   | `Base64("AQIDBA==")`                        |
| `tunnel_ips`            | Array[IP]      | Public and private IPs for VPN endpoints.                                     | `["203.0.113.1", "192.168.56.1/24"]`       |
| `auth_method`           | Enum           | Authentication mechanism (Certificate, OAuth, MFA).                            | `"TLS_CERT"`, `"OIDC"`                     |
| `routing_policy`        | Enum           | Routing method (Static, Dynamic BGP, Auto).                                    | `"DynamicBGP"`, `"Static"`                 |
| `mtu`                   | Integer        | Maximum Transmission Unit for packets.                                         | `1400`                                      |
| `log_retention`         | Integer (days) | Days to retain VPN connection logs.                                           | `90`                                        |
| `compliance_standards`  | Array[String]  | Applicable compliance frameworks.                                              | `["PCI_DSS", "GDPR"]`                      |

---

### **3.2 Site-to-Site VPN Schema**
| **Field**               | **Type**       | **Description**                                                                 | **Example Values**                          |
|-------------------------|----------------|-------------------------------------------------------------------------------|---------------------------------------------|
| `peer_gateway`          | String         | IP/Hostname of the remote VPN gateway.                                        | `"198.51.100.2"`                            |
| `pre_shared_key`        | String (Base64) | Shared secret for IKE authentication (rotated annually).                       | `Base64("shared-secret")`                   |
| `bgp_asn`               | Integer        | Autonomous System Number for BGP routing.                                      | `64512`                                     |
| `advertised_cidrs`      | Array[String]  | Subnets to advertise via BGP.                                                  | `["10.0.0.0/16", "172.16.0.0/12"]`         |
| `failover_peers`        | Array[IP]      | Secondary gateway IPs for redundancy.                                          | `["203.0.113.2"]`                          |
| `health_check_url`      | String         | Endpoint for VPN gateway health monitoring.                                    | `"https://gw-health/api/v1/status"`         |

---

## **4. Query Examples**

### **4.1 Query VPN Gateway Configuration (Terraform)**
```hcl
resource "azurerm_virtual_network_gateway" "corp_vpn" {
  name                = "corp-vpn-gw"
  location            = "eastus"
  resource_group_name = "security-rg"

  type     = "Vpn"
  sku_name = "VpnGw2"

  ip_configuration {
    subnet_id = azurerm_subnet.vpn_subnet.id
    public_ip_address_id = azurerm_public_ip.vpn_gw_pip.id
  }

  vpn_client_configuration {
    address_pool = "10.1.0.0/24"
    protocol_type = "IKEv2"
    revoke_certs_on_logoff = true
    auth_type = "Certificate"
    root_certificate {
      name = "corp-ca-root"
      public_cert_data = filebase64("corp-ca.cer")
    }
  }
}
```

---

### **4.2 Query Site-to-Site VPN (AWS CLI)**
```bash
aws ec2 create-vpn-gateway-connection \
    --vpn-gateway-id vgw-12345678 \
    --customer-gateway-id cgw-abcdef12 \
    --type ipsec.1 \
    --static-routes-config {
        "StaticRoutes": [
            {
                "DestinationCidrBlock": "10.0.0.0/16",
                "BgpAsn": 64512
            }
        ]
    } \
    --pre.shared-secret "MySuperSecretKey" \
    --tunnel-inspection-routing "enable"
```

---

### **4.3 Query VPN User Authentication (OpenVPN)**
```ini
# /etc/openvpn/server.conf
auth-user-pass-verify /etc/openvpn/user-auth.sh via-env
client-config-dir /etc/openvpn/ccd
<ca>
-----BEGIN CERTIFICATE-----
...
-----END CERTIFICATE-----
</ca>
client-cert-not-required
auth SHA256
cipher AES-256-GCM
user nobody
group nogroup
```

**Script (`/etc/openvpn/user-auth.sh`):**
```bash
#!/bin/sh
USER=$3
PASS=$(echo "$3" | tr -d '\n')

# Verify MFA token via OAuth2 (e.g., Azure AD)
TOKEN=$(curl -s -X POST "https://login.microsoftonline.com/$TenantID/oauth2/v2.0/token" \
    -d "client_id=$ClientID" \
    -d "scope=api://$ClientID/.default" \
    -d "client_secret=$Secret" \
    -d "grant_type=password" \
    -d "username=$USER" \
    -d "password=$PASS" \
    -d "mfa_code=$MFA_TOKEN")

if [ -z "$TOKEN" ]; then
    exit 1
fi

exit 0
```

---

## **5. Related Patterns**

| **Pattern**                     | **Description**                                                                 | **When to Use**                                                                 |
|----------------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Identity & Access Management]** | Centralized IAM with **SSO, MFA, and RBAC**.                            | When integrating VPN with **Okta, Azure AD, or Keycloak**.                      |
| **[Network Micro-Segmentation]**  | Isolate traffic between workloads using **NSGs, Firewalls, or eBPF**.     | To enforce **least-privilege access** in hybrid/multi-cloud.                   |
| **[Zero-Trust Networking]**      | **BeyondCorp** model with **continuous authentication and device posture checks**. | For **cloud-native** or **SOC2-compliant** environments.                      |
| **[Encrypted Data at Rest]**     | **TDE (Transparent Data Encryption) or KMS** for databases.               | When protecting **sensitive data** (e.g., **PCI-sensitive fields**).           |
| **[Disaster Recovery for VPN]**  | **Multi-region failover** with **active-active gateways**.                | For **high-availability** VPN deployments in **multi-cloud setups**.            |

---

## **6. Further Reading**
- [NIST SP 800-110: Guide to VPNs](https://csrc.nist.gov/publications/detail/sp/800-110/final)
- [OWASP VPN Security Guide](https://owasp.org/www-project-vpn-security-guide/)
- [AWS VPN Best Practices](https://aws.amazon.com/blogs/networking-and-content-delivery/amazon-vpn-best-practices/)
- [Zero Trust Network Access (ZTNA) by Gartner](https://www.gartner.com/en/documents/3999466/gartner-market-guide-zero-trust-network-access)

---
**Last Updated: [MM/DD/YYYY]**
**Version: 1.3**