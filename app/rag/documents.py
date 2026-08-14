"""
Curated AWS Cloud Knowledge Documents for CloudSage RAG Knowledge Base.
Contains authoritative, structured documentation covering EC2, S3, CloudWatch, IAM, and FinOps.
"""

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class KnowledgeDocument(BaseModel):
    document_id: str
    title: str
    category: str
    source: str = "AWS Documentation"
    url: str
    content: str
    keywords: List[str] = Field(default_factory=list)


# Curated Knowledge Base Dataset
KNOWLEDGE_DOCUMENTS: List[KnowledgeDocument] = [
    # ==========================================================================
    # 1. Amazon EC2
    # ==========================================================================
    KnowledgeDocument(
        document_id="doc_ec2_basics",
        title="Amazon EC2 Fundamentals & Architecture",
        category="EC2",
        source="AWS Documentation — Amazon EC2 User Guide",
        url="https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html",
        keywords=["ec2", "virtual machine", "instance", "ami", "compute", "elastic compute cloud", "cloud computing"],
        content="""Amazon Elastic Compute Cloud (Amazon EC2) provides scalable computing capacity in the AWS Cloud. Using Amazon EC2 eliminates the need to invest in hardware upfront, allowing developers to build and deploy applications faster.

Core Amazon EC2 concepts:
- Instances: Virtual computing environments running Linux or Windows.
- Amazon Machine Images (AMIs): Preconfigured templates for instances that package the operating system and additional software.
- Instance Types: Various combinations of CPU, memory, storage, and networking capacity designed to optimize workloads.
- Key Pairs: Secure login credentials for instances (AWS stores the public key, and you store the private key).
- Storage Volumes: Amazon Elastic Block Store (Amazon EBS) provides persistent block storage volumes for instances.
- Security Groups: Virtual stateful firewalls that control incoming and outgoing network traffic.
- Regions and Availability Zones: Physical locations across the globe where resources are hosted to achieve fault tolerance.

Instances can be launched with various purchasing options including On-Demand, Savings Plans, Reserved Instances, and Spot Instances."""
    ),
    KnowledgeDocument(
        document_id="doc_ec2_instance_types",
        title="EC2 Instance Types and Families",
        category="EC2",
        source="AWS Documentation — Amazon EC2 Instance Types",
        url="https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-types.html",
        keywords=["instance types", "t3", "c6i", "r6i", "m6i", "compute optimized", "memory optimized", "general purpose", "burstable"],
        content="""Amazon EC2 provides a wide selection of instance types optimized to fit different use cases. Instance types comprise varying combinations of CPU, memory, storage, and networking capacity.

Major EC2 Instance Families:
1. General Purpose (e.g., T3, T4g, M6i, M6g): Balanced compute, memory, and networking resources. Ideal for web servers, small databases, and code repositories. T-series instances are burstable, providing a baseline CPU performance with the ability to burst above the baseline using CPU credits.
2. Compute Optimized (e.g., C6i, C6g, C7g): High-performance processors. Ideal for compute-intensive applications such as high-performance web servers, batch processing, scientific modeling, and dedicated gaming servers.
3. Memory Optimized (e.g., R6i, R6g, X2gd): Fast performance for workloads that process large datasets in memory. Ideal for in-memory databases (Redis, Memcached), relational databases, and real-time big data analytics.
4. Storage Optimized (e.g., I3, I3en, D2): High sequential read and write access to very large datasets on local storage. Ideal for NoSQL databases (Cassandra, MongoDB), data warehousing, and distributed file systems.
5. Accelerated Computing (e.g., P4, G5): Hardware accelerators or GPUs for machine learning training, inference, and graphics-intensive workloads."""
    ),
    KnowledgeDocument(
        document_id="doc_ec2_security_groups",
        title="EC2 Security Groups and Network Access Rules",
        category="EC2",
        source="AWS Documentation — Amazon EC2 Security Groups",
        url="https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html",
        keywords=["security group", "firewall", "inbound rules", "outbound rules", "ports", "cidr", "stateful firewall", "network security"],
        content="""An Amazon EC2 security group acts as a virtual, stateful firewall for your EC2 instances to control incoming and outgoing network traffic.

Key Security Group Characteristics:
- Stateful Filtering: If you send a request from your instance, the response traffic is automatically allowed to flow back regardless of inbound rules. Conversely, if inbound traffic is allowed, responses are allowed outbound automatically.
- Default Behavior: When you create a security group, it has no inbound rules (all incoming traffic is blocked by default) and an outbound rule that permits all IPv4/IPv6 outbound traffic.
- Allow Rules Only: You can specify allow rules, but you cannot specify deny rules. Any traffic not explicitly allowed is denied by default.
- Rule Parameters: Each rule specifies the protocol (TCP, UDP, ICMP), port range (e.g., port 80 for HTTP, port 443 for HTTPS, port 22 for SSH), and source/destination CIDR block or another security group ID.
- Multiple Associations: You can attach multiple security groups to a single instance, and attach a single security group to multiple instances.

Comparison with Network ACLs (NACLs):
Security groups operate at the instance/ENI level and are stateful. Network ACLs operate at the subnet level and are stateless (requiring explicit inbound and outbound rule pairing)."""
    ),
    KnowledgeDocument(
        document_id="doc_ec2_availability_zones",
        title="AWS Regions, Availability Zones, and High Availability",
        category="EC2",
        source="AWS Documentation — Regions and Availability Zones",
        url="https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html",
        keywords=["availability zone", "region", "fault tolerance", "multi-az", "high availability", "disaster recovery", "az"],
        content="""Amazon cloud computing resources are housed in highly available data center facilities across the world categorized into Regions and Availability Zones (AZs).

- AWS Region: A separate geographic area (e.g., us-east-1 in N. Virginia, eu-west-1 in Ireland). Each Region is completely isolated from other Regions to achieve maximum fault tolerance and stability.
- Availability Zone (AZ): One or more discrete data centers with redundant power, networking, and connectivity in an AWS Region. Each AZ is isolated from failures in other AZs, but connected via ultra-low-latency private fiber networking.
- Multi-AZ Architecture: By launching EC2 instances across multiple Availability Zones, you can protect your applications from the failure of a single data center.
- Elastic Load Balancing (ELB): Distributes incoming application traffic across multiple EC2 instances in multiple Availability Zones to ensure uninterrupted availability."""
    ),
    KnowledgeDocument(
        document_id="doc_ec2_cpu_troubleshooting",
        title="Common Causes of High EC2 CPU Utilization & Troubleshooting",
        category="EC2",
        source="AWS Knowledge Center — Troubleshooting High EC2 CPU",
        url="https://aws.amazon.com/premiumsupport/knowledge-center/ec2-cpu-utilization-spike/",
        keywords=["cpu utilization", "high cpu", "spike", "troubleshoot cpu", "t3 credits", "runaway process", "top", "cloudwatch cpu"],
        content="""High CPU utilization on Amazon EC2 instances can degrade application performance, increase response latency, or cause instance unresponsiveness.

Common causes of high EC2 CPU utilization:
1. Runaway or Unoptimized Software Processes: Infinite loops, blocking I/O threads, unindexed database queries, or memory leaks causing high garbage collection overhead.
2. Traffic Spikes: Sudden surges in incoming user requests or API calls exceeding the compute capacity of the instance.
3. Insufficient Instance Sizing: Workloads running on undersized instance types (e.g., t3.micro handling enterprise production web traffic).
4. CPU Credit Exhaustion on Burstable Instances (T2/T3/T4g): When a burstable instance exhausts its CPU credits in standard mode, CPU performance is throttled back to the baseline level (e.g., 20% for t3.medium), causing queued tasks to consume 100% of the baseline.
5. Background Cron Jobs and Antivirus Scans: Periodic batch jobs or security agents consuming sudden processor bursts.

Remediation Steps:
- Identify top processes using OS tools (`top`, `htop`, or Windows Resource Monitor).
- Set up CloudWatch Alarms to trigger notifications when CPU utilization exceeds 80% for 5 minutes.
- Use Auto Scaling Groups to scale out additional instances automatically during high demand.
- Vertically scale to a larger instance type (e.g., from t3.medium to c6i.xlarge) or transition to Compute-Optimized instances."""
    ),

    # ==========================================================================
    # 2. Amazon S3
    # ==========================================================================
    KnowledgeDocument(
        document_id="doc_s3_basics",
        title="Amazon S3 Object Storage Fundamentals",
        category="S3",
        source="AWS Documentation — Amazon S3 User Guide",
        url="https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html",
        keywords=["s3", "simple storage service", "bucket", "object storage", "blob", "durability", "availability", "storage"],
        content="""Amazon Simple Storage Service (Amazon S3) is an object storage service offering industry-leading scalability, data availability, security, and performance.

Key S3 Concepts:
- Buckets: Containers for objects stored in Amazon S3. Bucket names must be globally unique across all AWS accounts worldwide.
- Objects: The fundamental entities stored in Amazon S3, consisting of object data (file content) and metadata (key-value pairs describing the object).
- Keys: The unique identifier for an object within a bucket (e.g., `photos/2026/vacation.jpg`).
- Flat Hierarchy: S3 has a flat object structure rather than a traditional hierarchical file system; prefixes containing slashes `/` simulate folders in user interfaces.
- Durability & Availability: Amazon S3 Standard is designed for 99.999999999% (11 9's) of data durability across multiple Availability Zones."""
    ),
    KnowledgeDocument(
        document_id="doc_s3_storage_classes",
        title="Amazon S3 Storage Classes and Tiering Differences",
        category="S3",
        source="AWS Documentation — Amazon S3 Storage Classes",
        url="https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html",
        keywords=["storage classes", "s3 standard", "glacier", "intelligent-tiering", "glacier deep archive", "infrequent access", "s3 tiering"],
        content="""Amazon S3 offers a range of storage classes tailored for different data access patterns, performance requirements, and cost budgets.

1. S3 Standard: Designed for frequently accessed data. Provides millisecond access, high throughput, and 11 9's durability. Highest storage cost per GB.
2. S3 Intelligent-Tiering: Automatically optimizes storage costs by moving data between three access tiers (Frequent, Infrequent, Archive Instant) when access patterns change, with zero performance impact or operational overhead.
3. S3 Standard-Infrequent Access (S3 Standard-IA): For data accessed less frequently but requiring rapid millisecond access when needed. Lower storage fee than Standard, but charges a per-GB retrieval fee.
4. S3 One Zone-Infrequent Access (S3 One Zone-IA): Stores data in a single Availability Zone at 20% lower cost than Standard-IA. Suitable for re-creatable secondary backups.
5. S3 Glacier Instant Retrieval: Archive storage delivering lowest-cost storage for rarely accessed data with immediate millisecond retrieval.
6. S3 Glacier Flexible Retrieval: Secure, low-cost archive storage with retrieval times ranging from minutes (Expedited) to 3-5 hours (Standard) or 5-12 hours (Bulk free).
7. S3 Glacier Deep Archive: Lowest-cost storage class across all cloud providers. Designed for long-term data retention (7-10+ years) with retrieval times within 12-48 hours."""
    ),
    KnowledgeDocument(
        document_id="doc_s3_lifecycle_policies",
        title="Amazon S3 Lifecycle Policies & Storage Cost Optimization",
        category="S3",
        source="AWS Documentation — Managing S3 Lifecycle",
        url="https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html",
        keywords=["lifecycle policy", "transition", "expiration", "s3 cost reduction", "archive data", "storage rules", "bucket lifecycle"],
        content="""An S3 Lifecycle configuration is a set of rules that define actions applied by Amazon S3 to a group of objects throughout their lifespan.

Two Types of Lifecycle Actions:
1. Transition Actions: Define when objects transition from one S3 storage class to another.
   - Example: Move objects from S3 Standard to S3 Standard-IA 30 days after creation, then transition to S3 Glacier Flexible Retrieval after 90 days.
2. Expiration Actions: Define when objects expire and are automatically deleted permanently by Amazon S3.
   - Example: Automatically delete temporary upload logs or incomplete multipart uploads after 14 days.

Best Practices:
- Apply prefix or tag filters to target specific datasets.
- Clean up expired object delete markers and incomplete multipart uploads to eliminate hidden storage charges.
- Combine lifecycle transitions with S3 Versioning to expire noncurrent object versions while retaining current versions."""
    ),

    # ==========================================================================
    # 3. Amazon CloudWatch
    # ==========================================================================
    KnowledgeDocument(
        document_id="doc_cloudwatch_fundamentals",
        title="Amazon CloudWatch Monitoring, Metrics, and Telemetry",
        category="CloudWatch",
        source="AWS Documentation — Amazon CloudWatch User Guide",
        url="https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html",
        keywords=["cloudwatch", "metrics", "dimensions", "telemetry", "monitoring", "cpuutilization", "datapoints", "observability"],
        content="""Amazon CloudWatch provides real-time monitoring and observability of AWS resources and the applications you run on AWS.

Core CloudWatch Components:
- Metrics: Fundamental data point variables representing time-ordered telemetry (e.g., EC2 `CPUUtilization`, `NetworkIn`, `DiskReadBytes`). Metrics are retained for up to 15 months.
- Dimensions: Name/value pairs that uniquely identify a metric (e.g., `InstanceId=i-03fa78bc91204d8ef`).
- Statistics: Metric aggregations over specified periods including Average, Sum, Minimum, Maximum, and Percentiles (p90, p99).
- Periods: The length of time associated with a specific CloudWatch statistic (e.g., 60 seconds, 300 seconds).

Basic Monitoring vs Detailed Monitoring:
- Basic Monitoring: Enabled by default for EC2 instances at no extra charge, publishing metrics at 5-minute intervals.
- Detailed Monitoring: Optional configuration providing 1-minute metric intervals for faster alerting and automated scaling."""
    ),
    KnowledgeDocument(
        document_id="doc_cloudwatch_alarms",
        title="Amazon CloudWatch Alarms and Automated Actions",
        category="CloudWatch",
        source="AWS Documentation — Using CloudWatch Alarms",
        url="https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html",
        keywords=["cloudwatch alarm", "alarm states", "ok", "insufficient_data", "sns", "autoscaling", "threshold", "alerting"],
        content="""A CloudWatch alarm watches a single metric over a specified time window and performs one or more automated actions based on the value of the metric relative to a defined threshold.

Alarm States:
- OK: The metric is within the defined acceptable threshold.
- ALARM: The metric has breached the threshold for the specified number of evaluation periods.
- INSUFFICIENT_DATA: The alarm has just started, metric data is not available, or not enough datapoints have arrived to determine state.

Automated Actions Triggered by Alarms:
- Amazon SNS Notifications: Send email, SMS, or webhook messages to engineers and Slack channels.
- EC2 Auto Scaling: Automatically scale out (add instances) or scale in (terminate instances) based on demand.
- EC2 Instance Actions: Stop, terminate, reboot, or recover failing EC2 virtual machines."""
    ),

    # ==========================================================================
    # 4. AWS Identity and Access Management (IAM)
    # ==========================================================================
    KnowledgeDocument(
        document_id="doc_iam_least_privilege",
        title="AWS IAM Principles, Policies, and Least Privilege",
        category="IAM",
        source="AWS Documentation — IAM Best Practices",
        url="https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html",
        keywords=["iam", "least privilege", "iam policy", "role", "user", "permissions", "access control", "json policy", "security"],
        content="""AWS Identity and Access Management (IAM) is a web service that helps you securely control access to AWS compute, storage, and database resources.

Principle of Least Privilege:
The security standard of granting only the minimum permissions required to perform a specific task, and nothing more. Practicing least privilege prevents accidental resource deletion, unauthorized access, and limits the blast radius of compromised credentials.

Key IAM Constructs:
- IAM Users: An identity with long-term credentials representing a person or service.
- IAM Groups: A collection of IAM users used to specify permissions for multiple users at once.
- IAM Roles: An identity with temporary security credentials (STS) that can be assumed by applications running on EC2, AWS services (like Lambda), or federated users.
- IAM Policies: JSON documents that explicitly define permissions.

Structure of a JSON IAM Policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["ec2:DescribeInstances", "s3:ListAllMyBuckets"],
      "Resource": "*"
    }
  ]
}
```
Rule of Evaluation: By default, all requests are denied. An explicit allow overrides the default deny, but an explicit deny always overrides any allow."""
    ),

    # ==========================================================================
    # 5. AWS Cost Management & FinOps
    # ==========================================================================
    KnowledgeDocument(
        document_id="doc_cost_optimization",
        title="AWS Cost Optimization Strategies and FinOps Principles",
        category="Cost Management",
        source="AWS Well-Architected Framework — Cost Optimization Pillar",
        url="https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html",
        keywords=["cost optimization", "finops", "reduce aws bill", "savings plans", "reserved instances", "idle resources", "rightsizing", "spend"],
        content="""Cost Optimization is a key pillar of the AWS Well-Architected Framework, focused on running cloud systems to deliver business value at the lowest price point.

Core Strategies to Reduce AWS Spend:
1. Rightsizing Compute Resources: Analyze CloudWatch CPU and memory metrics to identify underutilized instances and downsize them (e.g., migrating an instance averaging 4% CPU from t3.large to t3.small saves ~50%).
2. Stopping or Scheduling Idle Resources: Automatically power off non-production development and staging environments during nights and weekends.
3. Purchasing Savings Plans and Reserved Instances (RIs): Commit to a consistent amount of usage (1 or 3-year term) in exchange for discounts of up to 72% over On-Demand rates.
4. Enabling S3 Intelligent-Tiering & Lifecycle Rules: Move unaccessed objects from S3 Standard to Glacier to slash storage charges by up to 80-95%.
5. Identifying and Deleting Unattached Resources: Clean up unattached EBS volumes, unassociated Elastic IPs (which incur hourly idle charges), and obsolete EBS snapshots.
6. Using AWS Cost Explorer: Track daily unblended spend, identify top cost drivers, and establish anomaly alerts."""
    ),
    KnowledgeDocument(
        document_id="doc_cost_explorer_guide",
        title="AWS Cost Explorer & Spending Analysis",
        category="Cost Management",
        source="AWS Documentation — Analyzing Costs with Cost Explorer",
        url="https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html",
        keywords=["cost explorer", "unblended cost", "billing", "service breakdown", "spend analysis", "cost drivers", "monthly bill"],
        content="""AWS Cost Explorer is a tool that enables you to visualize, understand, and manage your AWS costs and usage over time.

Key Features of Cost Explorer:
- Historical and Forecasted Spend: View data for up to the last 12 months, analyze current-month spending rate, and forecast spend for the next 3 months.
- Service-by-Service Breakdown: Group and filter costs by Service (e.g., EC2, RDS, S3), Linked Account, Region, Usage Type, or Custom Cost Allocation Tags.
- Unblended vs Blended Rates: Unblended costs represent the actual standalone charge for each specific resource.
- Anomaly Detection: Automatically identify unexpected cost spikes caused by runaway workloads, unclosed development loops, or configuration errors."""
    )
]


def get_all_documents() -> List[KnowledgeDocument]:
    """Returns the complete curated knowledge base dataset."""
    return KNOWLEDGE_DOCUMENTS


def get_document_by_id(doc_id: str) -> Dict[str, Any]:
    """Finds a specific document by its ID."""
    for doc in KNOWLEDGE_DOCUMENTS:
        if doc.document_id == doc_id:
            return doc.model_dump()
    return {}
