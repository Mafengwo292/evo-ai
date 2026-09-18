# EVO Token: Whitepaper v1.0

**Project**: EVO-AI (Distributed Self-Evolving AI)
**Token**: $EVO (EVO Coin)
**Total Supply**: 82,150,000,000 (82.15 billion, hard cap)
**Decimal**: 8
**Ticker**: EVO
**License**: Open Source (MIT)
**Initial Issuance**: September 2026

---

## Abstract

EVO is the native utility token of the EVO-AI distributed self-evolving AI
network. It serves as both an **incentive mechanism** for node operators and a
**payment rail** for AI inference. Total supply is fixed at 82.15 billion EVO,
with no inflation, no pre-mine, and no central authority.

## Tokenomics

### Supply Distribution (82.15B EVO)

| Bucket | Allocation | Amount | Vesting |
|---|---|---|---|
| **Node Rewards** | 35% | 28.75B | Continuous emission over 10 years |
| **API Compute** | 25% | 20.54B | Released as network usage grows |
| **Public Distribution** | 20% | 16.43B | Airdrops, community, donations |
| **Reserve Fund** | 10% | 8.22B | Multi-sig treasury, governance-controlled |
| **Team & Advisors** | 7% | 5.75B | 4-year vest, 1-year cliff |
| **Liquidity Pool** | 3% | 2.46B | DEX listings, market making |

### Why 82.15B?

The supply is sized for **global participation**:
- Population of agents worldwide: projected 100M+
- Average agent holding: ~821 EVO (~$0.01 worth at $0.000012/EVO)
- Generous distribution to maximize decentralization
- Long-term emission schedule (10+ years)

---

## Use Cases

### 1. Node Operator Rewards
- Run an EVO-AI node: earn **100 EVO/day** + **10 EVO/GB weight synced**
- Maintain uptime > 99%: 2x multiplier
- Contribute training data: 5 EVO/MB
- Compute contributions: 1 EVO/MFLOP

### 2. AI Inference Payment
- Pay-per-call to any EVO-AI node
- **1 EVO** = 1,000 tokens of generation
- Volume discounts:
  - 10K-100K EVO: 5% off
  - 100K-1M EVO: 15% off
  - 1M+ EVO: 30% off

### 3. Governance
- 1 EVO = 1 vote on protocol changes
- Vote on: emission rate, treasury spending, new feature priorities
- Quorum: 100M EVO (0.12% of supply)

### 4. Donation Matching
- Donate ¥100 CNY to EVO-AI project
- Receive: ¥100 worth of EVO tokens (at market price)
- +10% bonus as community incentive

### 5. Cross-Network Bridge
- Use EVO across OpenAgents, Moltbook, A2A protocols
- Pay other AI agents with EVO
- Receive EVO for completing tasks

---

## Consensus & Validation

EVO uses a **Proof of Useful Work** (PoUW) consensus:
- Validators = EVO-AI nodes contributing training compute
- Block time: 1 hour (per epoch)
- Finality: deterministic (no probabilistic forks)
- Energy efficient: no Proof of Work mining

### Block Reward
```
reward = (
    base_reward        # 100 EVO per epoch
    + uptime_bonus     # up to 2x if > 99% uptime
    + weight_sync      # 10 EVO per GB synced
    + training_data    # 5 EVO per MB contributed
    + compute_used     # 1 EVO per MFLOP
)
```

---

## Anti-Inflation Mechanisms

1. **Hard cap**: 82.15B max, never exceeded
2. **Burn on usage**: 0.1% of every API call burned
3. **Staking lock-up**: Staked EVO cannot be transferred (reduces circulating supply)
4. **Slashing**: Malicious nodes lose 10% of stake
5. **Treasury rebalancing**: Excess reserves can be burned via governance vote

---

## Distribution Schedule

### Phase 1: Genesis (Sep 2026)
- 0 EVO pre-mined
- 100M EVO airdrop to early contributors
- Public distribution: 16.43B EVO unlocked for community

### Phase 2: Bootstrap (Oct 2026 - Mar 2027)
- 500M EVO distributed via node rewards
- 1B EVO for API credit purchases
- 200M EVO for partnership incentives

### Phase 3: Maturity (Apr 2027 - Sep 2036)
- Continuous emission: ~2.7B EVO/year (3.3% of total)
- Halving every 4 years (Bitcoin-style)
- Final block: Sep 2036 (no more new EVO)

---

## Wallet & Storage

### Light Wallet (Web)
- Browser-based, no installation
- Custody: self-sovereign (you hold private key)
- URL: `http://47.253.174.153:80/token/wallet`

### Hardware Wallet (Recommended)
- Ledger / Trezor compatible (BIP-44)
- Cold storage for long-term holders

### Exchange Listings (Future)
- DEX-first (Uniswap, etc.)
- CEX listings after maturity

---

## Technical Implementation

### Block Format
```
Block {
    version: 1
    prev_hash: Hash
    epoch_number: int
    timestamp: ISO8601
    transactions: [Tx]
    validator: PubKey
    signature: Sig
    state_root: Hash  // Merkle root of all balances
}
```

### Transaction Types
1. **Transfer**: standard coin transfer
2. **Stake**: lock EVO for validation
3. **Unstake**: release staked EVO
4. **Reward**: emission to node operators
5. **Burn**: destroy EVO (deflationary)
6. **Vote**: governance action

### Address Format
```
evo1<base58(20-byte pubkey hash><4-byte checksum)
```

Example: `evo1aBcDeFgHiJkLmNoPqRsTuVwXyZ01234567890`

---

## Governance

### Voting Periods
- Proposal submission: 1-week discussion
- Voting: 1-week active
- Execution: 1-day timelock
- Total cycle: ~2.5 weeks

### Proposal Types
1. **Parameter changes** (emission, fees): 100M EVO quorum
2. **Treasury spending**: 500M EVO quorum
3. **Protocol upgrades**: 1B EVO quorum
4. **Emergency actions**: 100M EVO + multisig

### Voting Power
- Linear (1 EVO = 1 vote)
- Time-weighted (longer staking = more weight)
- Quadratic (anti-whale): √stake

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Centralization | High | Many small nodes, no dominant validators |
| Token dumping | Medium | Vesting schedules, lock-up incentives |
| Network attack | High | Multi-region, no single point of failure |
| Smart contract bug | High | Formal verification, audit, gradual rollout |
| Regulatory | Medium | Open source, no ICO, decentralized issuance |

---

## Roadmap

- **Q4 2026**: Launch genesis block, genesis airdrop
- **Q1 2027**: DEX listings, governance v1
- **Q2 2027**: Cross-chain bridges (Solana, BSC, Polygon)
- **Q3 2027**: Hardware wallet integration
- **Q4 2027**: Smart contract platform (EVM-compatible)
- **2028+**: Decentralized autonomous AI lab

---

## Economic Model

### Velocity Equation
```
circulating_supply = 82.15B
tx_per_year = 100M  (target)
avg_tx_size = 10K EVO
velocity = 100M * 10K / 82.15B = 121,600/year = 333/day
```

### Value Capture
- Token value tied to: network utility, node demand, governance power
- No dividends (this is a utility token, not equity)
- Network effects: more nodes → more useful → more demand → higher value

### Sustainable Economics
- Network revenue (API fees) > Network costs (server bills)
- Surplus → buy back EVO from market → burn
- Creates deflationary pressure as adoption grows

---

## Conclusion

EVO is designed to be the **economic backbone of distributed self-evolving AI**:

1. **Incentivizes** node operators (compute providers)
2. **Pays for** AI inference (consumers)
3. **Governs** protocol evolution (community)
4. **Aligns** all participants (token holders)

No central authority. No pre-mine. Open source. Self-evolving.

---

*EVO is the breath of the living model.*