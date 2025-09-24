# Overview

This guide explains an example of building an **NSPS connector** in **Python** using **FastAPI**.  
The connector receives events from **NSPS**, validates and processes the payload, and then forwards the enriched data to an external system (in this example — **Google Sheets**).  
It also demonstrates how to implement **Bearer token authentication** and how to construct proper responses for **NSPS**, ensuring events are handled correctly.

You can find the full example repository here: [WTL HLR-HSS Connector](https://gitlab.portaone.com:8949/read-only/wtl_hlr_hss_connector)
