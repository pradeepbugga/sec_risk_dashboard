# SEC Risk Intelligence

#### Demo

You can find a demo of this project [here](https://huggingface.co/spaces/Prad33pb/SEC_Risk_Intelligence).

### Goal

   Traditionally, financial analysts have measured and predicted the performance of companies through structured data (i.e. metrics such as revenue, P/L, margins, EBITDA).  However, this numerical information provides an incomplete picture of a company's position as it lacks the semantic context of industry and macroeconomic sentiment, real-time news, and qualtitative insights into management strategy and corporate governance.  Some examples of valuable, non-numerical (or "unstructured") data include brand reptuation, changes in leadership, and pending litigation.  By harnessing and integrating unstructured data with recent advances in AI (specifically transformers and LLMs), we will be able to provide both more accurate and real-time information to the financial industry.  

   In this project, I specifically look at risk exposure of the semiconductor industry (namely 8 representative companies in the last 8 years) via unstructured 10-K narrative sections.  I not only hope to compare how a company's risk allocation varies with time, but also how that risk varies across the industry, potentially highlighting insightful differences.  Success of this project entails building a robust end-to-end pipeline but also validating the final output against all the information we have beyond the 10-K text. 

### Pipeline 

  #### 1. Text Ingestion



