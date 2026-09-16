# MTGMate — Use Case Diagram

```mermaid
flowchart LR
    User(("User"))

    subgraph MTGMate Desktop App
        UC1(("Enter MTGMate Details"))
        UC2(("Browse to Collection.csv"))
        UC3(("Run Buylist Automation"))
        UC4(("Handle Login & reCAPTCHA"))
        UC5(("Track Progress"))
        UC6(("Pause at 300-Card Cap"))
        UC7(("Generate output.csv"))
    end

    subgraph MTGMate Website
        UC9(("Review Buylist Cart"))
        UC10(("Remove Unwanted Cards"))
        UC11(("Complete Sale"))
    end

    User --> UC1
    User --> UC2
    User --> UC3
    User --> UC5
    User --> UC6
    User --> UC9
    User --> UC10
    User --> UC11

    UC3 -.include.-> UC4
    UC3 -.include.-> UC5
    UC3 -.include.-> UC7
    UC3 -.include.-> UC6
    UC3 -.leads to.-> UC9
    UC9 --> UC10
    UC10 --> UC11
    UC7 -.compare against.-> UC9
```

## Actor
- **User** 

## Use Cases (current)
- Configure Collection & Settings 
- Find cards to sell
- Run Buylist Automation 
- Handle Login 
- Track Progress 
- Pause at 300-Card Cap
- Generate output.csv

