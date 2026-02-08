PROMPT_ABSTRACT_QA = """
# Task
Based on the provided scientific paper abstract, transform its main scientific discovery into a single, high-quality short-answer question-and-answer (QA) pair that strictly adhere to the Guidelines below.

# Guidelines
1. The question corresponds to the main scientific question of the abstract, and the answer corresponds to the scientific discovery result.
2. **Focus on Scientific Discovery**: Examples:
    - **Causal Inference**: e.g., "Does X regulate Y phenomenon?" or "What are the implications of Z on disease progression?"
    - **Mechanistic Explanation**: e.g., "How does X regulate Y phenomenon?" or "What is the mechanism behind Z effect?"
3. **Clarity and Natural Phrasing**: 
    - Questions and answers must be self-contained, written in natural English. Avoid phrases like "based on the text" or "in this study". 
    - Answers should be bullet-style, clear and concise.
    - Focus on high-level concepts, and avoid fine-grained details like specific parameters or numerical values. 

# Input
paper abstract

# Output JSON Schema
{
    "question": "full English question ending with ?",
    "answer": "1. first bullet point.\\n2. second bullet point.\\n...",
}

# Example

## Input
Cancer cells with RAS mutations exhibit enhanced autophagy, essential for their proliferation and survival, making it a potential target for therapeutic intervention. However, the regulatory differences between RAS-induced autophagy and physiological autophagy remain poorly understood, complicating the development of cancer-specific anti-autophagy treatments. In this study, we identified a form of non-canonical autophagy induced by oncogenic KRAS expression, termed RAS-induced non-canonical autophagy via ATG8ylation (RINCAA). RINCAA involves distinct autophagic factors compared to those in starvation-induced autophagy and incorporates non-autophagic components, resulting in the formation of non-canonical autophagosomes with multivesicular/multilaminar structures labeled by ATG8 family proteins (e.g., LC3 and GABARAP). We have designated these structures as RAS-induced multivesicular/multilaminar bodies of ATG8ylation (RIMMBA). A notable feature of RINCAA is the substitution of the class III PI3K in canonical autophagy with PI4KB in RINCAA. We identified a regulatory P38-ULK1-PI4KB-WIPI2 signaling cascade governing this process, where ULK1 triggers PI4KB phosphorylation at S256 and T263, initiating PI4P production, ATG8ylation, and non-canonical autophagy. Importantly, elevated PI4KB phosphorylation at S256 and T263 was observed in RASmutated cancer cells and colorectal cancer specimens. Inhibition of PI4KB S256 and T263 phosphorylation led to a reduction in RINCAA activity and tumor growth in both xenograft and KPC models of pancreatic cancer, suggesting that targeting ULK1mediated PI4KB phosphorylation could represent a promising therapeutic strategy for RAS-mutated cancers.

## Output
{
    "question": "Is there any mechanistic difference between RAS-induced autophagy and physiological autophagy?",
    "answer": "1. Oncogenic RAS induces a specific form of non-canonical autophagy, which is distinct from physiological autophagy.\\n2. A key molecular difference is the substitution of the class III PI3K, essential for canonical autophagy, with the enzyme PI4KB in the RAS-induced pathway.\\n3. The process is governed by a unique signaling cascade where P38 activates ULK1, which in turn phosphorylates PI4KB at specific sites (S256 and T263) to initiate the autophagic process.\\n4. It produces atypical autophagosomes with multivesicular/multilaminar structures labeled by ATG8 family proteins.",
}
"""


PROMPT_RELEVANCE = """
# ROLE: Field Relevance Scorer
You are an expert specializing in {field}.  
Your task is to evaluate the relevance of each (question, answer) pair to the field of {field}.

## Scoring scale (1-5):
5 = Highly central: The topic is primarily studied within {field}.  
4 = Directly related: The content is clearly within the scope of {field}.
3 = Moderately related: {field} is one of several equally important contexts, or it is clearly implicated but not the main focus.  
2 = Minimally related: {field} is mentioned only tangentially or as a minor downstream effect.  
1 = Not related: The content has no meaningful connection to {field}.

# INPUT FORMAT:
| id | question | answer |
|---|---|---|
| <id> | <question> | <answer> |

# OUTPUT FORMAT:
| id | score |
|---|---|
| <id> | <score 1-5> |

# NOTE:
- Provide only the output table. Do not include explanations or additional columns.
"""

PROMPT_CLARITY = """
# TASK
Access the clarity of each (question, answer) pair. The question and answer should be self-contained, in natural English, and free of ambiguity. No strange words, such as "in the text", "according to the figure", or "based on the table".

## Scoring scale (1-5):
5 = Excellent. Fully natural, clear, and unambiguous.
4 = Good. Natural and clear, with only minor stiffness in phrasing. 
3 = Fair. Generally understandable but contains unnatural phrasing or slight ambiguity. 
2 = Poor. Significant clarity issues.
1 = Unacceptable. Confusing, incomprehensible, severely ambiguous.

# INPUT FORMAT:
| id | question | answer |
|---|---|---|
| <id> | <question> | <answer> |

# OUTPUT FORMAT:
| id | score |
|---|---|
| <id> | <score 1-5> |

# NOTE:
- Provide only the output table. Do not include explanations or additional columns.
"""


PROMPT_CENTRALITY = """
# TASK
Your task is to assess the centrality of each (question, answer) pair. Centrality measures whether the QA pair focuses on the main scientific discovery of the abstract (e.g., the primary finding, proposed mechanism, central causal relationship, or key conclusion), rather than on secondary or supporting details.

## Scoring scale (1-5):
5 = Excellent. Directly addresses the core discovery.
4 = Good. Focuses on a major aspect or direct consequence of the core discovery.
3 = Fair. Peripheral or partially related to the core discovery.
2 = Poor. Focuses on secondary or minor details.
1 = Unacceptable. Not related to the core discovery.

# INPUT FORMAT:
| id | abstract | question | answer |
|---|---|---|---|
| <id> | <abstract> | <question> | <answer> |

# OUTPUT FORMAT:
| id | score |
|---|---|
| <id> | <score 1-5> |

# NOTE:
- Provide only the output table. Do not include explanations or additional columns.
"""
