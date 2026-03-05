# SEC Risk Intelligence

#### Demo

You can find a demo of this project [here](https://huggingface.co/spaces/Prad33pb/SEC_Risk_Intelligence).

### Goal

   Traditionally, financial analysts have measured and predicted the performance of companies through structured data (i.e. metrics such as revenue, P/L, margins, EBITDA).  However, this numerical information provides an incomplete picture of a company's position as it lacks the semantic context of industry and macroeconomic sentiment, real-time news, and qualtitative insights into management strategy and corporate governance.  Some examples of valuable, non-numerical (or "unstructured") data include brand reptuation, changes in leadership, and pending litigation.  By harnessing and integrating unstructured data with recent advances in AI (specifically transformers and LLMs), we will be able to provide both more accurate and real-time information to the financial industry.  

   In this project, I specifically look at risk exposure of the semiconductor industry (namely 8 representative companies in the last 8 years) via unstructured 10-K narrative sections.  I not only hope to compare how a company's risk allocation varies with time, but also how that risk varies across the industry, potentially highlighting insightful differences.  Success of this project entails building a robust end-to-end pipeline but also validating the final output against all the information we have beyond the 10-K text. 

   Note: A critical component of our strategy is using structure-aware chunks that contain the text in the context of headings.  A lot of code early in our pipeline is devoted to properly parsing these chunks, but the benefit downstream is that clustering of "heading + text" embeddings becomes cleaner.   

### Pipeline 

  #### 1. HTML Ingestion

The first step is to use EdgarTools to get the HTML files corresponding to all relevant filings.  From the DOM (Document Object Model) structure of an HTML, I will be able to extract structure-aware text chunks.


  #### 2. Text Ingestion
The next step is to get the text corresponding to the Risk Factors section.  For a 10-K filing, this is explicitly in "Item 1A." but for a 20-F filing (relevant for foreign companies like TSMC), this is somewhere within "Item 3".  We found that just using EdgarTools was insufficient across our filings, so I developed a 4-level fallback system:
   - Anchor-Based Extraction (using the anchor / a tags to find the sections that ToC points to)
   - Flattened Anchor Extraction (first flattens deeply nested HTML structure before finding anchors)
   - Structural Extraction (looks for headers in p, div and td tags via regex)
   - Title/Regex Extraction (raw text search for section titles)

Based on this fallback, you can see that our strategy handles files with the most structure (anchors present) to the least structure (mostly textual).

 #### 3. Identifying Beginning / End Nodes
 The next step is to use the text we extracted in the previous step as a means of identifying the beginning and end HTML node.  Establishing the node boundaries is essential for then capturing the underlying hierarchy within a section.

####  4. Block Parsing and Scoring
 Once we have identified the relevant section in HTML, we extract each sub-structure ("block") in HTML that contains text.  This also involves de-noising (flattening table information, connecting text across page breaks, removing headers/footers, and capturing bulleted lists that are noted in HTML as tables).  

####  5. Block Scoring / Heading Identification
Next, we have to score each of the blocks we identified in the previous step to identify headings.   Across filings, we observed that headings were visually emphasized in some manner (font size, caps, bold, italics, underline, color).  So we first established a baseline of font size, weight, and color across the entire section, then boosted the score of text blocks that were sufficiently different.  (Note: a number of edge cases have associated rules such as short lines ending in a colon before a bulleted list).  We are able to capture the majority of headings this way (the exception being sub-headings that are visually emphasized but are unusually long above our word count threshold).  

#### 6. 

    




