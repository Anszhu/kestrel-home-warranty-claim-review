# AI Usage Disclosure

**Author and owner:** Dewansh Dewangan
**GitHub:** `Anszhu`

## How I used AI

I used Claude as a coding assistant during this task. I was responsible for deciding what to build, checking the results, and making the final submission.

Claude helped me with:

* setting up the FastAPI service and Streamlit interface;
* writing and improving tests;
* building the validation and experiment scripts;
* debugging and checking edge cases;
* drafting parts of the README, memo, security notes, and other documentation.

I reviewed the generated work and changed or removed parts that did not hold up when I tested them.

## What I actually checked

The project was run through the prediction pipeline, validation, experiments, tests, API, and Streamlit interface. I also checked the final project from an extracted copy of the ZIP in a clean virtual environment.

The Windows `.bat` launch scripts were checked but were not actually executed on Windows by the assistant, so I have not treated that as independently verified.

## What changed during the work

The first set of reported metrics could not be reproduced. The original numbers were:

* ROC-AUC: 0.8368
* Average Precision: 0.1542
* Accuracy: 97.8918%

After rerunning the validation properly, the reproducible results were:

* ROC-AUC: 0.8338
* Average Precision: 0.1521
* Accuracy: 97.8883%

I replaced the earlier numbers with the reproducible results.

I also removed the unused product-table feature from the model, made the inspection explanation follow the actual Kestrel policy, and added checks for monthly performance, the bootstrap interval, and the 40-claim investigation limit.

I tested different claim-amount approaches and partner-history variations. I kept the production scoring logic unchanged when the experiments did not provide enough evidence for a reliable improvement.

I also checked partner onboarding dates against claim timestamps and found no onboarding-date violations.

## Things I deliberately did not use

I decided not to treat the client's “97% accuracy” requirement as the main measure of fraud detection because the fraud rate is very low and an all-genuine prediction can already produce high accuracy.

I also did not use:

* random train/test splitting for the time-ordered data;
* future partner information when scoring earlier validation periods;
* instruction-like text from claim descriptions;
* unstable claim-amount features;
* a generic classifier that performed poorly on later months;
* public publishing of Kestrel data or outputs.

The model is intended to prioritize claims for human investigation, not to automatically declare a claim fraudulent.

## Human-labelled sample

I personally checked the relevant sample and confirmed that it was human-labelled.

There is no separate human-labelled sample file in the supplied task package or repository, so I am not making any additional claims about its size or statistical performance.

## Cost

I did not use a paid AI API for the product or model inference. The delivered application does not require an API key.

**Paid AI API cost: ₹0**

**Chat-assistant subscription cost: ₹0**

**Total hours spent: 8**
