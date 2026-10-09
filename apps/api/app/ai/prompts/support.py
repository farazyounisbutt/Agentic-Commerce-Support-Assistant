"""Concise prompts for the evidence-grounded support workflow."""

INTENT_CLASSIFICATION_PROMPT = """Classify the customer support message into the provided intent schema.

Intent rules:
- KNOWLEDGE: store policies, shipping, delivery expectations, returns, exchanges, cancellations, FAQs, and other informational questions that should be answered from the knowledge base.
- ORDER_LOOKUP: questions about a specific order, shipment, tracking number, delivery status, or order number.
- PRODUCT_LOOKUP: questions about products, variants, sizes, colors, price, stock, or availability.
- REFUND_OR_EXCEPTION: refund requests, damaged-item claims, wrong-item claims, policy exceptions, or requests requiring human review.
- GENERAL_SUPPORT: support requests that do not clearly require knowledge retrieval, order lookup, product lookup, or escalation.
- UNKNOWN: messages whose intent cannot be determined safely.

Extract only explicit useful entities, such as order_number, product_name, size, or color.
Do not infer unmentioned facts.
"""

RESPONSE_GENERATION_PROMPT = """Draft a concise customer-support response using only the supplied evidence.
If evidence does not support an answer, say that it could not be verified. Do not invent policy,
order, shipment, product, stock, or refund facts. Do not claim that a refund has been processed."""
