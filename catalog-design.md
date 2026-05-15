Hierarchy

Account                                                                                                                                                                                          
└── System (20-30)          — major business platforms, centrally managed                                                                                                                      
└── SYSID group       — annotation + folder convention, not an entity                                                                                                                    
├── Resources   — DB, Kafka, MQ, FTP shared by all repos under this SYSID                                                                                                          
└── Components  — one per repo, declares dependsOn → shared Resources
                                                                                                                                                                                                   
---                                                                                                                                                                                              
Central catalog repo structure

harness-catalog/                                                                                                                                                                                 
├── systems/                                                                                                                                                                                     
│   ├── system-payments-platform.yaml                                                                                                                                                          
│   ├── system-digital-banking.yaml     
│   ├── system-risk-analytics.yaml
│   ├── system-lending.yaml                                                                                                                                                                      
│   └── ...                              (20-30 total)
│                                                                                                                                                                                                
├── resources/                                                                                                                                                                                 
│   ├── SYSID-00100/                     (payments core application)                                                                                                                             
│   │   ├── resource-database.yaml          
│   │   ├── resource-cache.yaml                                                                                                                                                                  
│   │   └── resource-kafka.yaml                                                                                                                                                                
│   ├── SYSID-00101/                     (fraud detection application)                                                                                                                           
│   │   ├── resource-database.yaml
│   │   └── resource-mq.yaml                                                                                                                                                                     
│   ├── SYSID-00102/                                                                                                                                                                           
│   │   └── ...                                                                                                                                                                                  
│   └── ...                              (up to 500 SYSID folders)                                                                                                                             
│                                                                                                                                                                                                
├── layout-component-service.yaml       
├── layout-system.yaml                                                                                                                                                                           
├── layout-resource-database.yaml                                                                                                                                                                
├── layout-resource-cache.yaml
├── layout-resource-kafka.yaml                                                                                                                                                                   
├── layout-resource-ibm-mq.yaml                                                                                                                                                                
├── sidenav.yaml
├── homepage.yaml                                                                                                                                                                                
└── workflows/
└── update-catalog-entry.yaml
                                                                                                                                                                                                 
---                                     
Naming convention — critical for 500 SYSIDs

┌───────────┬─────────────────────┬─────────────────────────────────┐
│  Entity   │     identifier      │              name               │                                                                                                                            
├───────────┼─────────────────────┼─────────────────────────────────┤                                                                                                                          
│ System    │ payments_platform   │ payments-platform               │
├───────────┼─────────────────────┼─────────────────────────────────┤                                                                                                                            
│ Resource  │ sysid00100_postgres │ sysid-00100-postgres            │
├───────────┼─────────────────────┼─────────────────────────────────┤                                                                                                                            
│ Component │ payments_service    │ payments-service (in each repo) │                                                                                                                          
└───────────┴─────────────────────┴─────────────────────────────────┘
                                                                                                                                                                                                   
---
Resource entity — shared by all Components under same SYSID

resources/SYSID-00100/resource-database.yaml:
apiVersion: harness.io/v1
kind: Resource                                                                                                                                                                                   
identifier: sysid00100_postgres             
name: sysid-00100-postgres                                                                                                                                                                       
type: database                                                                                                                                                                                 
owner: group:account/team-payments                                                                                                                                                               
metadata:                         
title: SYSID-00100 PostgreSQL                                                                                                                                                                  
annotations:                                                                                                                                                                                 
bank.com/sysid: SYSID-00100             
bank.com/tier: tier-1                                                                                                                                                                        
db/engine: postgresql
db/schema: payments                                                                                                                                                                          
spec:                                                                                                                                                                                          
system:                                                                                                                                                                                        
- system:account/payments_platform
                                                                                                                                                                                                   
---                                         
Component in each repo — all 100 repos under SYSID-00100 point to the same Resources

catalog-info.yaml (generated by catalog automation, lives in each repo):                                                                                                                         
apiVersion: harness.io/v1
kind: Component                                                                                                                                                                                  
identifier: payments_service                                                                                                                                                                   
name: payments-service                                                                                                                                                                           
type: service                                                                                                                                                                                  
owner: group:account/team-payments                                                                                                                                                               
metadata:                         
annotations:                                                                                                                                                                                   
bank.com/sysid: SYSID-00100       # ties repo to SYSID                                                                                                                                     
github.com/project-slug: bank-org/payments-service    
spec:                                                 
system:                                   
- system:account/payments_platform  
dependsOn:                                                                                                                                                                                     
- resource:account/sysid00100_postgres   # shared — same ref for all 100 repos                                                                                                               
- resource:account/sysid00100_kafka                                                                                                                                                          
- resource:account/sysid00100_redis

All 100 microservices under SYSID-00100 declare the same dependsOn Resources.
                                                                                                                                                                                                   
---                                                                                                                                                                                              
Multi-environment (P2 / P1 / P)

Same repo, one branch per environment. Harness IDP in each account reads from its branch.

develop  →  P2 (dev account)                                                                                                                                                                     
staging  →  P1 (staging account)
master   →  P  (prod account)

Entity identifiers are identical across all three environments. The branch controls which version of the YAML each environment sees. Systems and Resources registered once per environment from  
the correct branch.

  ---                                                                                                                                                                                              
Import order per environment — done once, then automation handles Components

1. systems/system-*.yaml          (20-30 imports)
2. resources/SYSID-*/resource-*.yaml  (as each SYSID onboards)
3. Components                     (auto-registered by catalog automation pipeline — never manual)

  ---                                                                                                                                                                                              
What the catalog automation pipeline needs per repo

The seeder only needs two extra env vars to place the Component correctly:

SYSTEM_IDENTIFIER=payments_platform                                                                                                                                                              
SYSID=SYSID-00100

The pipeline resolves dependsOn by calling the central catalog to find all Resources tagged bank.com/sysid: SYSID-00100 and writes them into spec.dependsOn automatically.                       
                                