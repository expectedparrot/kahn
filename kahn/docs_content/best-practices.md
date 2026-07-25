# Scenario Planning Best Practices

A reference guide for facilitating high-quality scenario planning exercises using the kahn CLI. Drawn from the work of Herman Kahn, Pierre Wack (Shell), Peter Schwartz (GBN), and the Oxford Scenario Planning Approach.

---

## The Purpose of Scenario Planning

Scenario planning is **not forecasting**. It does not attempt to predict the future. Instead, it:

1. **Expands perception** — reveals assumptions decision-makers don't know they're making
2. **Stress-tests strategy** — identifies options that work across multiple futures, not just the expected one
3. **Builds preparedness** — creates shared language and mental models for responding to change
4. **Surfaces blind spots** — the most valuable scenario is often the one nobody in the room expected

The output of a good exercise is not "the answer" but a richer understanding of the decision landscape and a strategy that is robust to surprise.

---

## Phase 1: Environmental Scanning

### What Makes a Good Force

A well-defined force is:

- **External** — it acts on the organization from outside, not within it. "Our culture is risk-averse" is internal. "Regulatory burden on innovation is increasing" is external.
- **Specific** — "Technology is changing" is too vague. "Foundation models are commoditizing specialized NLP capabilities" is specific enough to reason about.
- **Falsifiable** — you could look at the world in 5 years and determine whether this force played out. "The world is uncertain" is not falsifiable.
- **Directional** — a force describes movement, not a state. "AI exists" is a state. "AI capability is improving exponentially while cost is dropping" is directional.

### Common Mistakes

| Mistake | Example | Fix |
|---------|---------|-----|
| Confusing forces with strategies | "Invest in AI" | Reframe as "AI capability improvement is accelerating" |
| Vague platitudes | "The world is becoming more complex" | Get specific: which complexity, where, affecting whom? |
| Biased framing | "Decline of traditional education" | Neutral: "Shift in education delivery models" (decline is one pole, not the force) |
| Missing domains | All forces are technological | Actively scan political, social, economic, environmental, legal |
| Too few uncertainties | Only 1-2 uncertainty forces | Need 3-4+ high-impact uncertainties to have genuine choice in CU selection |

### PESTEL Coverage Guide

Aim for at least 3 of these 6 domains:

- **Political**: Government policy, regulation, geopolitics, institutional governance
- **Economic**: Funding models, market dynamics, labor markets, inequality, trade
- **Social**: Demographics, cultural values, public attitudes, workforce expectations
- **Technological**: AI/ML, platforms, infrastructure, digital transformation, biotech
- **Environmental**: Climate, sustainability mandates, resource constraints, energy transition
- **Legal**: IP law, liability, compliance, accreditation, data privacy

---

## Phase 2: Critical Uncertainty Selection

### The Independence Test

The two critical uncertainties MUST be logically independent. This is the most common failure mode in scenario planning.

**Test**: Ask four questions:
1. If CU1 resolves to pole A, does that make CU2's pole A more likely? 
2. If CU1 resolves to pole A, does that make CU2's pole B more likely?
3. If CU1 resolves to pole B, does that make CU2's pole A more likely?
4. If CU1 resolves to pole B, does that make CU2's pole B more likely?

If the answer to any of these is clearly "yes," the uncertainties are correlated and the 2x2 matrix will have one or more implausible quadrants. Choose a different pair.

**Example of correlated pair (bad)**:
- CU1: "Will AI regulation be strict or permissive?"
- CU2: "Will AI development accelerate or stagnate?"
- Problem: Strict regulation makes stagnation more likely → correlated

**Example of independent pair (good)**:
- CU1: "Will AI regulation be strict or permissive?"
- CU2: "Will public trust in institutions increase or decrease?"
- These can combine in all four ways without contradiction

### What Makes Good Poles

| Quality | Good Pole | Bad Pole |
|---------|-----------|----------|
| Extreme | "Federal funding for universities drops 50%" | "Funding decreases somewhat" |
| Plausible | "All major courses have AI tutors by 2035" | "AI achieves consciousness" |
| Specific | "Top 20 universities capture 80% of global enrollment via online" | "Education is different" |
| Value-neutral | "Knowledge production shifts to industry labs" | "Universities fail" |

### The 2x2 Matrix

The matrix creates 4 scenario quadrants:

```
                    CU2: Pole A
                        |
           Scenario 1   |   Scenario 2
                        |
   CU1: Pole A --------+-------- CU1: Pole B
                        |
           Scenario 3   |   Scenario 4
                        |
                    CU2: Pole B
```

Every quadrant must be plausible. If one feels impossible, the uncertainties are likely correlated.

---

## Phase 3: Scenario Construction

### Writing Effective Narratives

**Structure a narrative around**:
1. **The trigger** — what event or shift in the late 2020s set this world in motion?
2. **The mechanism** — how did the critical uncertainties resolve to create this world?
3. **Daily life** — what does a typical day/year look like for the people and organizations in this world?
4. **Winners and losers** — who thrives, who struggles, and why?
5. **The predetermined elements** — how do the trend forces manifest in this particular scenario?

**Narrative quality checklist**:
- [ ] Written in present tense ("It is 2040. Universities operate...")
- [ ] Tells a story, not a list of bullet points
- [ ] Internally consistent with axis positions
- [ ] Includes all predetermined elements (trends)
- [ ] Contains both opportunities and threats
- [ ] Feels like a genuinely different world from the other scenarios
- [ ] A reader could explain how the world got here from today
- [ ] Specific enough to make strategic decisions against

### The "Official Future" Trap

Most organizations have an "official future" — the implicit expected trajectory that planning assumes. In scenario planning, this official future should NOT be one of the four scenarios. It should sit somewhere in the middle of the matrix.

If one of your scenarios feels like "what everyone expects," your poles aren't extreme enough or your uncertainties aren't uncertain enough.

### Predetermined Elements

Trend forces appear in ALL four scenarios because they are predictable regardless of how uncertainties resolve. For example:
- "Global population aging" is a trend — it appears in all scenarios
- "Whether aging populations drive increased healthcare spending or cost-cutting innovation" is an uncertainty — it differs across scenarios

Make sure each narrative explicitly addresses how predetermined elements manifest in that particular scenario context.

### Naming Scenarios

Good names make scenarios memorable and discussable. After the exercise, you want people to say "What do we do if we're heading toward 'The Great Unbundling'?" not "What about Scenario 3?"

| Good Names | Bad Names |
|------------|-----------|
| "The Great Unbundling" | "High AI / Low Regulation" |
| "Fortress Academy" | "Scenario A" |
| "The Credential Bazaar" | "Disrupted Education Future" |
| "Silicon Quad" | "Optimistic Technology Scenario" |

### Signals: Early Warning Systems

The real operational value of scenario planning comes from signals — observable indicators that a particular scenario is emerging. Good signals:

- **Are observable today or soon** — "Check Crunchbase for EdTech funding trends quarterly"
- **Are specific and measurable** — "3+ top-20 universities launch AI-native degree programs" not "universities adopt AI"
- **Are leading indicators** — they precede the scenario, not describe it
- **Have a clear observation method** — specify where and how to watch for the signal
- **Differentiate between scenarios** — a signal that appears in all scenarios isn't useful

---

## Phase 4: Option Evaluation

### Designing Strategic Options

Good options for evaluation are:

- **Distinct** — each option represents a fundamentally different strategic posture, not a variation
- **Actionable** — specific enough that the organization could begin implementing within a year
- **Complete** — each option is a coherent strategy, not a single tactic
- **Spanning** — the set should cover the space of reasonable strategies (at least one conservative, one aggressive, one hedging)

### The Evaluation Rating Scale

| Rating | Meaning | When to Use |
|--------|---------|-------------|
| **Robust** | The option thrives in this scenario — it's well-positioned for this world | The option directly addresses the conditions of this scenario |
| **Acceptable** | The option survives — it's not optimal but doesn't fail | The option is somewhat mismatched but has enough flexibility to adapt |
| **Fragile** | The option fails or backfires — this scenario exposes its weaknesses | The option's core assumptions are contradicted by this scenario |

### Interpreting Robustness Scores

- **Score > 0.75**: Highly robust — strong candidate for core strategy
- **Score 0.50-0.75**: Moderately robust — viable but may need hedging
- **Score < 0.50**: Fragile overall — only pursue if you have strong conviction about specific scenarios
- **Any "fragile" rating**: Flag for discussion — understand which scenarios break this option and whether those scenarios are plausible

### Strategy Recommendations

The output of the evaluation phase is typically one of these strategy archetypes:

1. **Robust Core**: One or two options score highly across all scenarios → make these the foundation
2. **Core + Hedge**: A robust option as the main strategy, plus a hedging option that preserves flexibility in the scenarios where the core is weakest
3. **Staged Commitment**: Start with hedging options, monitor signals, and commit to a bolder strategy as the scenario landscape clarifies
4. **Portfolio**: Pursue multiple options simultaneously (possible only if they don't conflict and resources allow)

---

## Common Pitfalls Across the Exercise

### 1. Rushing to Solutions
The most common mistake is treating scenario planning as a quick path to "the answer." The value comes from the structured exploration. If you skip to options without deeply understanding the uncertainty landscape, you'll just confirm existing strategy.

### 2. Scenarios That Are Too Similar
If your scenarios feel like minor variations on the same theme, your critical uncertainties aren't distinct enough. Step back and choose more divergent uncertainties.

### 3. Optimism Bias
Decision-makers naturally gravitate toward the scenario closest to their hopes. Ensure each scenario has both opportunities and threats, and give equal analytical attention to uncomfortable scenarios.

### 4. Ignoring Predetermined Elements
Trends that appear in all scenarios are easy to overlook but often contain the most actionable insights. If global population aging is a trend, every strategy should address it.

### 5. Confusing Robustness with Optimality
A robust strategy is not the best strategy in any single scenario — it's the strategy that performs acceptably across all of them. This is a feature, not a bug. The point is resilience to surprise.

### 6. Treating Scenarios as Predictions
Never assign probabilities to scenarios. The moment you say "Scenario 2 is 40% likely," you've collapsed back into forecasting and will under-invest in preparing for the other scenarios.

### 7. Insufficient Stakeholder Input
Scenario planning works best as a collaborative exercise. The agent facilitates structure and research, but domain expertise from the user is essential at every phase transition.

---

## References

- Kahn, H. & Wiener, A.J. (1967). *The Year 2000: A Framework for Speculation*
- Wack, P. (1985). "Scenarios: Uncharted Waters Ahead." *Harvard Business Review*
- Schwartz, P. (1991). *The Art of the Long View*
- van der Heijden, K. (2005). *Scenarios: The Art of Strategic Conversation*
- Ramirez, R. & Wilkinson, A. (2016). *Strategic Reframing: The Oxford Scenario Planning Approach*
- Schoemaker, P.J.H. (1995). "Scenario Planning: A Tool for Strategic Thinking." *Sloan Management Review*
