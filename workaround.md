workaround. Retrieve button to pull all the rows from backend. This solves one of the limitation.

⏺ Good instinct. ValidateAndFetch button solves the visibility half. Here's exactly what it can and cannot do:

  What the Retrieve button gives you:
  - Calls the backend, gets all 18 rows
  - Displays them as read-only reference so user knows what exists
  - User then uses the editable array below to declare only what they want to change

  What it still cannot do:
  - Pre-populate the editable array rows (no RJSF mechanism to inject API data into array items)

  ---
  Concrete implementation:

  Add a /apptier-names endpoint to the mock API returning a flat string (ContextViewer can't render arrays):

  // In mock-api — new endpoint
  r.GET("/apptier-names", func(c *gin.Context) {
      config := buildAppTierConfig()
      names := make([]string, 0, len(config))
      for k := range config {
          names = append(names, k)
      }
      sort.Strings(names)
      c.JSON(200, gin.H{"names": strings.Join(names, ", ")})
  })

  Workflow YAML pattern:

  # Step 1 — Retrieve button (ValidateAndFetch, field level NOT ui:options)
  retrieveAppTiers:
    title: Current App Tiers
    type: string
    ui:field: ValidateAndFetch
    button: Retrieve App Tiers
    path: proxy/mock-api/apptier-names
    method: GET
    setContextData:
      appTierNames: names

  # Step 2 — Display retrieved list
  appTierList:
    title: Available Repos
    type: string
    ui:field: ContextViewer
    readonly: true
    ui:options:
      getContextData: '{{formContext.appTierNames}}'

  # Step 3 — Editable array (user adds only rows they want to touch)
  appTiers:
    title: App Tier Changes
    description: Add rows to update existing repos or add new ones
    type: array
    items:
      type: object
      required: [repositoryName]
      properties:
        repositoryName:
          title: Repository Name
          type: string
          description: Copy name from the list above
        instanceSize:
          title: Instance Size
          type: string
          enum: [small, medium, large, xlarge]
        loadbalancer:
          title: Load Balancer
          type: string
          enum: [ALB, NLB, None]
        os:
          title: OS
          type: string
          enum: [linux, windows]

  ---
  User flow with this pattern:

  1. Click Retrieve App Tiers → sees "payments-service, fraud-service, ledger-service, ..."
  2. Adds one array item, copies payments-service from the display → edits instance size
  3. Adds another item, copies fraud-service → edits load balancer
  4. Adds a third item, types new-repo-19 → fills all fields

  Pipeline receives the array, distinguishes update vs. create by checking if the repo name exists in the master list.

  ---
  R



❯ can user update 2 rows and add a 3 row.

⏺ Yes. The type: array of objects with plain text/enum fields (no SelectFieldFromApi inside) does NOT have the override bug — each item is stored independently at its own array index.

  User clicks Add Item 3 times:

  ┌─────┬──────────────────┬──────────────┬──────────────┬────────────────────┐
  │  #  │  repositoryName  │ instanceSize │ loadbalancer │ What pipeline does │
  ├─────┼──────────────────┼──────────────┼──────────────┼────────────────────┤
  │ 1   │ payments-service │ large        │ ALB          │ Update existing    │
  ├─────┼──────────────────┼──────────────┼──────────────┼────────────────────┤
  │ 2   │ fraud-service    │ medium       │ NLB          │ Update existing    │
  ├─────┼──────────────────┼──────────────┼──────────────┼────────────────────┤
  │ 3   │ new-repo-19      │ small        │ None         │ Create new         │
  └─────┴──────────────────┴──────────────┴──────────────┴────────────────────┘

  Pipeline receives:
  [
    { "repositoryName": "payments-service", "instanceSize": "large", "loadbalancer": "ALB" },
    { "repositoryName": "fraud-service", "instanceSize": "medium", "loadbalancer": "NLB" },
    { "repositoryName": "new-repo-19", "instanceSize": "small", "loadbalancer": "None" }
  ]

  Pipeline logic: call /apptier-config/:repo — if it exists → update, if 404 → create. Three independent operations, no override.

  The override bug only happens with SelectFieldFromApi inside arrays. Plain type: string text fields and enum dropdowns inside array objects are fine.

===
Path 2 — Confirmed working but bounded: named field groups

  No arrays. Pre-define a fixed number of named change slots:

  change1:
    title: Change 1 — Repo
    type: string
    ui:field: SelectFieldFromApi
    ui:options:
      path: proxy/mock-api/apptier-options
      valueSelector: repositoryName
      labelSelector: repositoryName

  change1InstanceSize:
    title: Change 1 — Instance Size
    type: string
    enum: [small, medium, large]

  change2:
    title: Change 2 — Repo
    type: string
    ui:field: SelectFieldFromApi
    ui:options:
      path: proxy/mock-api/apptier-options
      valueSelector: repositoryName
      labelSelector: repositoryName

  change2InstanceSize:
    title: Change 2 — Instance Size
    type: string
    enum: [small, medium, large]

  newRepo:
    title: New Repo Name
    type: string

  newRepoInstanceSize:
    title: New Repo — Instance Size
    type: string
    enum: [small, medium, large]

  Each field has a unique name — zero override risk. Pipeline collects change1, change1InstanceSize, change2, change2InstanceSize, newRepo, newRepoInstanceSize, skips any that are empty.

  Limitation: capped at however many slots you pre-define (e.g. "update up to 3 existing, add up to 2 new"). Fine for most real-world use — how often does someone update 10 tiers in one go?

=====
Here is the safe path clearly:       

  ---                                         
  Safe: type: array of objects with plain type: string + enum fields
                                                                    
  Override bug is specific to SelectFieldFromApi inside arrays. Plain text and enum fields inside array objects store independently per index — no override. This is the reliable choice.          
                                              
  ┌────────────────────────────────────────┬───────────────┬─────────────────────────────┬─────────────────────┐                                                                                   
  │                Approach                │ Override risk │       Repo selection        │      Bounded?       │
  ├────────────────────────────────────────┼───────────────┼─────────────────────────────┼─────────────────────┤                                                                                   
  │ Array of objects — plain text + enum   │ None          │ User types name             │ No — unlimited rows │                                                                                   
  ├────────────────────────────────────────┼───────────────┼─────────────────────────────┼─────────────────────┤                                                                                   
  │ Named field groups (Path 2)            │ None          │ SelectFieldFromApi dropdown │ Yes — fixed slots   │                                                                                   
  ├────────────────────────────────────────┼───────────────┼─────────────────────────────┼─────────────────────┤
  │ SelectFieldFromApi inside array object │ Unknown       │ Dropdown                    │ No                  │
  └────────────────────────────────────────┴───────────────┴─────────────────────────────┴─────────────────────┘                                                                                   
                                                                                                                                                                                                   
  Recommended: array of objects with plain text repo name. Reasons:                                                                                                                                
  - No override risk — confirmed                                                                                                                                                                   
  - Unlimited rows — user adds as many as needed               
  - Handles update, add, delete in one form                                                                                                                                                        
  - Retrieve button provides the reference list so user knows what to type
                                                                                                                                                                                                   
  Named field groups are also safe but only use them if the business rule is genuinely bounded — e.g. "support team updates at most 3 tiers per request". Don't use them just to get dropdowns —
  the UX trade-off isn't worth it.            
                                                                                                                                                                                                   
  Path 1 (SelectFieldFromApi inside object property) — do not treat as safe until tested in a live workflow. It may work, but it is unconfirmed. Test it separately as an enhancement after the    
  base pattern is working.                                                                                                                                                                         
                                                                                                                                                                                                   
  ---                                                                                                                                                                                              
  The confirmed safe workflow structure:                       
                                                                                                                                                                                                   
  Page 1                                                       
    ├── retrieveAppTiers   (ValidateAndFetch button → calls /apptier-names)
    ├── appTierList        (ContextViewer → shows retrieved names)
    ├── updateTiers        (array of objects — repositoryName: string, config: enum)
    ├── deleteTiers        (array of objects — repositoryName: string only)                                                                                                                        
    └── addTiers           (array of objects — repositoryName: string, all config: enum)                                                                                                           
                                                                                                                                                                                                   
  No custom plugin. No override risk. All four operations covered. 

Exactly what the array pattern handles.

In one form submission:

updateTiers array — click Add Item twice:                                                                                                                                                        
Item 1: repositoryName = "app-tier-repo-2"  instanceSize = "Large"   loadbalancer = "NLB"                                                                                                        
Item 2: repositoryName = "app-tier-repo-5"  instanceSize = "Medium"  loadbalancer = "ALB"

addTiers array — click Add Item twice:                       
Item 1: repositoryName = "app-tier-repo-19"  os = "Linux"  instanceSize = "Small"  ...                                                                                                           
Item 2: repositoryName = "app-tier-repo-20"  os = "Linux"  instanceSize = "Medium" ...

Pipeline receives both arrays in one shot:

updateTiers: [                                                                                                                                                                                   
{ "repositoryName": "app-tier-repo-2", "instanceSize": "Large", "loadbalancer": "NLB" },                                                                                                       
{ "repositoryName": "app-tier-repo-5", "instanceSize": "Medium", "loadbalancer": "ALB" }                                                                                                       
]

addTiers: [                                                  
{ "repositoryName": "app-tier-repo-19", "os": "Linux", "instanceSize": "Small", ... },                                                                                                         
{ "repositoryName": "app-tier-repo-20", "os": "Linux", "instanceSize": "Medium", ... }
]

No limit on how many items per array. 

2 updates + 2 adds, or 5 updates + 1 add — same pattern, just more array items. The pipeline loops through each array independently.  