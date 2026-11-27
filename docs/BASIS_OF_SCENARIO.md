## Basis of the Scenario
  EquipTrack is an academic prototype developed for MIS 215 – Client-Server Computing. Its proposed client organization is the **Bicol University College of Industrial Technology (BUCIT) – Mechanical Technology Department**, located in Legazpi City, Albay, Philippines. The project focuses exclusively on departmental equipment borrowing and return transactions.

### Scenario and Participants
  The scenario involves student borrowers requesting equipment for a specified period and an equipment custodian, who may be a designated faculty member, managing approval, release and return.

The application implements two access roles:
- **Borrower:** Checks equipment availability, submits requests, cancels their own pending requests and views their borrowing history.
- **Custodian:** Approves or rejects requests, records equipment releases and returns, manages inventory and accounts, and reviews transaction and audit records.
The code also supports a faculty borrower classification within the borrower role. Whether this classification applies to the department requires confirmation.

### Workflow Basis
  The scenario follows the five core transactions implemented in the application:
1. Check equipment availability.
2. Submit a borrowing request.
3. Approve or reject the request.
4. Record the physical release of equipment.
5. Record its return and condition.
  The design distinguishes a pending request, an approved reservation and actual equipment custody. Application checks and database constraints prevent conflicting approved reservations and duplicate active loans. Recording a damaged return places the equipment in maintenance status.

### Evidence and Assumptions
  The revised project proposal establishes the intended departmental scope. The source code, database migrations and recorded tests establish the prototype’s implemented behavior.
The supplied materials do not establish the department’s current borrowing procedure, actual inventory, approval policies or existing operational problems. Therefore, this project does not claim that the department experiences equipment losses, delayed approvals or inaccurate records.
  Borrower eligibility, reservation rules, custodian designation and damage-handling procedures are modeled project rules that require departmental validation.

### Project Status
  EquipTrack is a developed academic prototype proposed for departmental consideration. Its implementation does not establish departmental adoption, authorization or production readiness.
  Academic demonstrations and testing use synthetic accounts, equipment and transaction records. Any institutional deployment would require confirmation of operating procedures, authorization and applicable data privacy responsibilities.
