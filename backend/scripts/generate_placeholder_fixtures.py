import json, os, sys
from pathlib import Path

# Add backend directory to path
backend_dir = r'C:\Users\USER\Documents\CODE\HACKATHONS\OPEN BUILD AI\backend'
sys.path.insert(0, backend_dir)
from app import schemas

OUT_DIR = Path(r'C:\Users\USER\Documents\CODE\HACKATHONS\OPEN BUILD AI\fixtures')
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODELS = [
    schemas.ModelDisclosure(
        role=schemas.ModelRole.EXTRACTION,
        model_id='meta-llama/Llama-3.1-8B-Instruct',
        provider='groq',
        license='Llama 3.1 Community License',
        license_url='https://www.llama.com/llama3_1/license/',
        parameter_count='8B'
    ),
    schemas.ModelDisclosure(
        role=schemas.ModelRole.EMBEDDING,
        model_id='BAAI/bge-small-en-v1.5',
        provider='fastembed-local',
        license='MIT',
        license_url='https://huggingface.co/BAAI/bge-small-en-v1.5',
        parameter_count='33M'
    ),
    schemas.ModelDisclosure(
        role=schemas.ModelRole.REFEREE,
        model_id='meta-llama/Llama-3.1-8B-Instruct',
        provider='groq',
        license='Llama 3.1 Community License',
        license_url='https://www.llama.com/llama3_1/license/',
        parameter_count='8B'
    ),
    schemas.ModelDisclosure(
        role=schemas.ModelRole.CONSENSUS_WRITER,
        model_id='meta-llama/Llama-3.1-8B-Instruct',
        provider='groq',
        license='Llama 3.1 Community License',
        license_url='https://www.llama.com/llama3_1/license/',
        parameter_count='8B'
    )
]

def make_radiology():
    papers_data = [
        ('p1', 'P1', 'Smith (2024)', 'Placeholder Paper 1: ResNet-50 on Curated Chest Radiographs', ['J. Smith', 'A. Doe'], 2024, 12, 'NIH ChestX-ray14 (curated n=1,200)', 'Supervised fine-tuning of ResNet-50', '94.2% Diagnostic Accuracy (AUC 0.96)', 'Evaluated only on clean, motion-free curated hospital archives.', 'ResNet-50 models surpass human clinician baselines under curated lab conditions.'),
        ('p2', 'P2', 'Adewale (2024)', 'Placeholder Paper 2: DenseNet-121 in Real-World Clinical Deployments', ['T. Adewale', 'O. Bello'], 2024, 14, 'Rural District Hospital Scans (n=3,400)', 'DenseNet-121 with uncalibrated field inputs', '68.4% Accuracy (AUC 0.72)', 'Severe sensitivity drop when encountering portable X-ray artifacts.', 'Deep architectures fail to maintain diagnostic parity on noisy clinical field data.'),
        ('p3', 'P3', 'Chen (2024)', 'Placeholder Paper 3: Vision Transformer Robustness under Motion Blur', ['L. Chen', 'M. Rossi'], 2024, 16, 'Synthetic Motion-Corrupted MIMIC-CXR (n=5,000)', 'ViT-Base with Patch-Level Attention Dropout', '88.1% Accuracy under 15% blur', 'Computationally prohibitive for low-power edge medical carts.', 'Attention mechanisms retain spatial diagnostic features better than convolutional backbones under motion blur.'),
        ('p4', 'P4', 'Kowalski (2025)', 'Placeholder Paper 4: Multi-Center Generalization of Pneumothorax Detectors', ['P. Kowalski', 'S. Lind'], 2025, 11, '4-Center Collaborative Radiography Cohort (n=8,200)', 'Ensemble ResNet + Swin Transformer with domain adversarial training', '91.3% Multi-Site Balanced Accuracy', 'Requires cross-site calibration to counter differing scanner manufacturer profiles.', 'Domain adaptation effectively bridges the performance gap across disparate radiographic hardware.'),
        ('p5', 'P5', 'Nwachukwu (2025)', 'Placeholder Paper 5: Low-Dose CT vs High-kV Radiography in Triage', ['C. Nwachukwu', 'D. Miller'], 2025, 13, 'Acute Pulmonary Admissions (n=950)', 'Comparative prospective diagnostic trial with expert consensus ground truth', 'High-kV Radiography missed 24% of occult lesions vs Low-Dose CT', 'Radiation dose was 4x higher in the CT cohort.', 'Plain radiography remains inadequate for early-stage ground-glass opacity screening compared to low-dose CT.'),
        ('p6', 'P6', 'Dubois (2025)', 'Placeholder Paper 6: Self-Supervised Pretraining for Pediatric Chest Scans', ['E. Dubois', 'V. Moreau'], 2025, 15, 'Pediatric Pneumonia Cohort (n=2,100)', 'DINOv2 self-supervised pretraining with pediatric fine-tuning', '89.7% Specificity on pediatric consolidations', 'Small sample size for rare congenital thoracic malformations.', 'Self-supervised representations learned on adult scans transfer robustly to pediatric radiology with minimal label tuning.'),
        ('p7', 'P7', 'Patel (2025)', 'Placeholder Paper 7: Radiologist-in-the-Loop Diagnostic Calibration', ['R. Patel', 'K. Gomez'], 2025, 10, 'Academic Teaching Hospital Double-Read Trial (n=4,000)', 'Interactive triage queue with confidence-weighted clinician routing', '18% Reduction in reading turnaround time; 96.1% joint accuracy', 'Clinicians displayed automation bias when model confidence was artificially high.', 'Human-AI collaborative triage outperforms either autonomous AI or unassisted human radiologists.'),
        ('p8', 'P8', 'Takahashi (2025)', 'Placeholder Paper 8: Edge Device Quantization for Portable X-Ray Units', ['H. Takahashi', 'Y. Sato'], 2025, 12, 'Field Bedside Portable Imaging Suite (n=1,500)', 'INT8 post-training quantization on Raspberry Pi / Jetson Orin', '0.4% AUC drop vs FP32 with 3.8x inference speedup', 'Battery thermal throttling observed after 45 consecutive scan evaluations.', 'INT8 quantization enables real-time bedside triage without meaningful loss in diagnostic discrimination.')
    ]
    
    papers = []
    claims = []
    
    for i, p in enumerate(papers_data):
        pid, short_lbl, cit_lbl, title, authors, yr, pages, dset, meth, metric, limit, conc = p
        paper = schemas.PaperMetadata(
            paper_id=pid,
            short_label=short_lbl,
            citation_label=cit_lbl,
            palette_index=i,
            source=schemas.PaperSource.DEMO,
            arxiv_id=None,
            filename=f'{pid}_radiology_placeholder.pdf',
            title=title,
            authors=authors,
            year=yr,
            page_count=pages,
            sections_found=[schemas.SectionName.ABSTRACT, schemas.SectionName.METHODOLOGY, schemas.SectionName.RESULTS, schemas.SectionName.CONCLUSION],
            dataset=dset,
            sample_size=f'n={1000 + i*500}',
            methodology=meth,
            primary_metric=metric,
            limitations=limit,
            core_conclusion=conc,
            extraction_model='meta-llama/Llama-3.1-8B-Instruct'
        )
        papers.append(paper)
        
        claim_defs = [
            (schemas.ClaimType.EMPIRICAL_RESULT, 'Diagnostic Accuracy', f'{short_lbl} reports primary diagnostic metric: {metric}.', metric, f'{pid}-c1', False, schemas.SectionName.RESULTS, 4, f'In our primary evaluation, {title} achieved {metric}.'),
            (schemas.ClaimType.METHOD, 'Methodological Design', f'{short_lbl} employs {meth} as its core approach.', None, f'{pid}-c2', False, schemas.SectionName.METHODOLOGY, 3, f'Our pipeline implements {meth} to ensure reproducible evaluation across test subsets.'),
            (schemas.ClaimType.CONCLUSION, 'Clinical Viability', f'{short_lbl} concludes: {conc}', None, f'{pid}-c3', False, schemas.SectionName.CONCLUSION, pages - 1, f'In conclusion, {conc}'),
            (schemas.ClaimType.LIMITATION, 'Operational Constraints', f'{short_lbl} observes key constraint: {limit}', None, f'{pid}-c4', False, schemas.SectionName.LIMITATIONS, pages - 2, f'A critical limitation of this work is: {limit}'),
            (schemas.ClaimType.EMPIRICAL_RESULT, 'Secondary Evaluation', f'{short_lbl} verifies secondary performance on {dset}.', 'Valid baseline', f'{pid}-c5', pid in ['p5', 'p8'], schemas.SectionName.RESULTS, 6, f'Secondary cross-validation confirms baseline consistency across {dset}.')
        ]
        
        for ctype, topic, stmt, mval, cid, is_gap, sec, pg, quote in claim_defs:
            claims.append(schemas.ExtractedClaim(
                claim_id=cid,
                paper_id=pid,
                claim_type=ctype,
                topic_hint=topic,
                statement=stmt,
                metric_value=mval,
                cluster_id='cl-1' if 'Accuracy' in topic or 'Viability' in topic else ('cl-2' if 'Method' in topic else 'cl-3'),
                is_research_gap=is_gap,
                provenance=schemas.Provenance(
                    paper_id=pid,
                    paper_title=title,
                    section=sec,
                    page_number=pg,
                    verbatim_quote=quote
                )
            ))

    def make_edge(src_cid, tgt_cid, rel, conf, sim, expl, cl_id):
        s_claim = next(c for c in claims if c.claim_id == src_cid)
        t_claim = next(c for c in claims if c.claim_id == tgt_cid)
        eid = f"e-{src_cid.replace('-', '')}-{tgt_cid.replace('-', '')}"
        return schemas.ClaimComparisonEdge(
            edge_id=eid,
            source_claim_id=src_cid,
            target_claim_id=tgt_cid,
            source=s_claim.provenance,
            target=t_claim.provenance,
            relation=rel,
            confidence=conf,
            cosine_similarity=sim,
            explanation=expl,
            cluster_id=cl_id,
            referee_model='meta-llama/Llama-3.1-8B-Instruct'
        )

    edges = [
        make_edge('p1-c1', 'p2-c1', schemas.RelationType.CONTRADICT, 0.92, 0.81, 'Smith (2024) asserts 94.2% diagnostic accuracy ready for clinical triage, whereas Adewale (2024) demonstrates an accuracy collapse to 68.4% on actual hospital scans with motion artifacts.', 'cl-1'),
        make_edge('p1-c3', 'p2-c3', schemas.RelationType.CONTRADICT, 0.95, 0.79, 'Smith claims models surpass human clinician baselines, but Adewale proves models fail to maintain diagnostic parity on noisy clinical field data.', 'cl-1'),
        make_edge('p3-c1', 'p4-c1', schemas.RelationType.AGREE, 0.88, 0.74, 'Both Chen (2024) and Kowalski (2025) find that modern architectural adaptations maintain robust accuracy (>88%) under distribution shifts.', 'cl-1'),
        make_edge('p1-c1', 'p6-c1', schemas.RelationType.AGREE, 0.84, 0.71, 'Dubois (2025) confirms Smith (2024) in finding high baseline accuracy (>89%) when leveraging strong pretrained vision representations.', 'cl-1'),
        make_edge('p2-c1', 'p3-c1', schemas.RelationType.METHODOLOGY_DELTA, 0.89, 0.77, 'Adewale tested uncalibrated DenseNet-121 on field artifacts yielding 68.4% accuracy, whereas Chen applied ViT with attention dropout yielding 88.1%, proving architectural choice drives resilience to blur.', 'cl-1'),
        make_edge('p1-c3', 'p7-c3', schemas.RelationType.METHODOLOGY_DELTA, 0.91, 0.73, 'Smith evaluates fully autonomous AI triage (94.2%), whereas Patel evaluates an interactive radiologist-in-the-loop collaborative workflow (96.1%), showing hybrid deployment mitigates false confidence.', 'cl-1'),
        make_edge('p1-c1', 'p8-c1', schemas.RelationType.METHODOLOGY_DELTA, 0.87, 0.69, 'Smith reports FP32 server inference, while Takahashi tests INT8 quantization on edge hardware, demonstrating minimal accuracy loss (0.4%) at the cost of thermal throttling constraints.', 'cl-3'),
        make_edge('p4-c4', 'p7-c4', schemas.RelationType.AGREE, 0.82, 0.68, 'Both Kowalski (2025) and Patel (2025) highlight that deployment success hinges on rigorous cross-scanner and clinician confidence calibration.', 'cl-2')
    ]
    
    gaps = [
        schemas.ResearchGap(
            signal='RESEARCH_GAP',
            gap_id='gap-p5-c5',
            claim_id='p5-c5',
            paper_id='p5',
            statement='Nwachukwu (2025) evaluates high-kV plain radiography against low-dose CT for occult ground-glass lesions, an imaging modality unexamined by any other paper in this set.',
            provenance=next(c.provenance for c in claims if c.claim_id == 'p5-c5'),
            best_match_similarity=0.43,
            reason='No claim in any other paper investigates comparative low-dose CT diagnostic benchmarks for occult thoracic lesions.'
        ),
        schemas.ResearchGap(
            signal='RESEARCH_GAP',
            gap_id='gap-p8-c5',
            claim_id='p8-c5',
            paper_id='p8',
            statement='Takahashi (2025) identifies battery thermal throttling on mobile X-ray edge hardware after 45 consecutive scans, an operational hardware factor unaddressed by algorithm-centric papers.',
            provenance=next(c.provenance for c in claims if c.claim_id == 'p8-c5'),
            best_match_similarity=0.38,
            reason='No claim in any other paper measures physical hardware thermal throttling or sustained edge-device battery drain during portable bedside triage.'
        )
    ]
    
    clusters = [
        schemas.TopicCluster(
            cluster_id='cl-1',
            label='Diagnostic Accuracy & Real-World Generalization',
            claim_ids=['p1-c1', 'p1-c3', 'p2-c1', 'p2-c3', 'p3-c1', 'p4-c1', 'p6-c1'],
            paper_ids=['p1', 'p2', 'p3', 'p4', 'p6'],
            mean_similarity=0.76
        ),
        schemas.TopicCluster(
            cluster_id='cl-2',
            label='Methodological Adaptation & Clinician Calibration',
            claim_ids=['p4-c4', 'p7-c3', 'p7-c4'],
            paper_ids=['p4', 'p7'],
            mean_similarity=0.71
        ),
        schemas.TopicCluster(
            cluster_id='cl-3',
            label='Hardware Constraints & Edge Deployment',
            claim_ids=['p1-c1', 'p8-c1', 'p8-c4'],
            paper_ids=['p1', 'p8'],
            mean_similarity=0.69
        )
    ]
    
    cross_pairs = 700
    candidate_pairs = 32
    referee_evaluated = 8
    pair_reduction = round(100 * (1 - candidate_pairs / cross_pairs), 1)
    
    consensus = schemas.ConsensusReport(
        consensus_score=56,
        executive_summary='Across the 8 analyzed radiology papers, strong empirical consensus exists that deep learning models achieve high diagnostic discrimination (>88%) under curated or domain-adapted settings. However, a major empirical contradiction divides clean lab studies (Smith 2024: 94.2%) from clinical field deployments (Adewale 2024: 68.4%), where uncalibrated scanner artifacts cause severe diagnostic degradation. Multi-center ensembling and radiologist-in-the-loop workflows consistently outperform autonomous triage.',
        agreed_findings=[
            'Modern neural architectures maintain diagnostic accuracy (>88%) when domain adaptation is applied (Chen 2024, Kowalski 2025).',
            'Pretrained self-supervised adult representations transfer effectively to pediatric radiography with minimal fine-tuning (Dubois 2025).'
        ],
        top_contradictions=[
            schemas.TopContradiction(
                edge_id='e-p1c1-p2c1',
                headline='Clinical readiness dispute: Smith (2024) reports 94.2% accuracy in clean archives, while Adewale (2024) finds performance drops to 68.4% on field hospital scans.'
            ),
            schemas.TopContradiction(
                edge_id='e-p1c3-p2c3',
                headline='Human clinician equivalence controversy: Lab benchmark superiority does not hold on noisy field inputs.'
            )
        ],
        gap_ids=['gap-p5-c5', 'gap-p8-c5'],
        recommended_next_steps=[
            'Standardize motion-artifact augmentation benchmarks across prospective radiography trials.',
            'Incorporate physical edge hardware thermal constraints into portable triage models.',
            'Mandate radiologist-in-the-loop confidence calibration before autonomous deployment.'
        ]
    )
    
    stats = schemas.AnalysisStats(
        paper_count=8,
        claim_count=40,
        cross_paper_pairs_total=cross_pairs,
        candidate_pairs=candidate_pairs,
        referee_pairs_evaluated=referee_evaluated,
        referee_calls=2,
        pair_reduction_pct=pair_reduction,
        stage_latency_ms=schemas.StageLatency(
            ingestion_ms=920,
            extraction_ms=6400,
            embedding_ms=85,
            clustering_ms=14,
            referee_ms=2100,
            consensus_ms=1350,
            total_ms=10869
        )
    )
    
    res = schemas.AnalysisResult(
        schema_version='1.0.0',
        analysis_id='demo-radiology',
        mode=schemas.AnalysisMode.DEMO,
        preset_id='radiology',
        fixture_provenance=schemas.FixtureProvenance.SYNTHETIC_PLACEHOLDER,
        generated_at='2026-10-26T21:00:00Z',
        papers=papers,
        claims=claims,
        clusters=clusters,
        edges=edges,
        gaps=gaps,
        consensus=consensus,
        stats=stats,
        models=MODELS,
        warnings=['This dataset is synthetic placeholder data for hackathon development. Honest open-source disclosure.']
    )
    return res

def make_llm_quant():
    papers_data = [
        ('p1', 'P1', 'Zheng (2024)', 'Placeholder Paper 1: GPTQ 4-Bit Instruction Following Evaluation', ['H. Zheng', 'Y. Wang'], 2024, 12, 'MMLU 5-shot & Alpaca-Eval', 'GPTQ 4-bit weight-only quantization', '0.8 point MMLU accuracy drop vs FP16', 'Context length capped at 2,048 tokens.', '4-bit weight-only quantization preserves standard benchmark reasoning within 1 point.'),
        ('p2', 'P2', 'Okonkwo (2024)', 'Placeholder Paper 2: AWQ Degradation under Long-Context Reasoning', ['C. Okonkwo', 'E. Vance'], 2024, 15, 'LongBench 32k context suite', 'Activation-aware Weight Quantization (AWQ) 4-bit', '7.9 point degradation at 32k tokens', 'Tested only dense decoder models (Llama-2/3).', 'Long-context reasoning is disproportionately vulnerable to low-bit quantization errors.'),
        ('p3', 'P3', 'Al-Mansoor (2024)', 'Placeholder Paper 3: Calibration Set Diversity in Weight-Only Quantization', ['K. Al-Mansoor', 'F. Tariq'], 2024, 11, 'RedPajama diverse subsets', 'Systematic calibration corpus variance testing', 'Perplexity variance of 1.4 across domains', 'English-centric calibration corpora only.', 'Calibration domain mismatch causes severe out-of-domain degradation in 4-bit models.'),
        ('p4', 'P4', 'Schneider (2025)', 'Placeholder Paper 4: Low-Rank Adaptation Mixed Precision Quantization', ['M. Schneider', 'G. Braun'], 2025, 14, 'GSM8k and HumanEval', 'QLoRA 4-bit NormalFloat with FP16 adapters', 'Matches full fine-tuning within 0.3%', 'Inference latency increases by 22% due to dequantization overhead.', '4-bit NormalFloat base with unquantized LoRA adapters eliminates mathematical reasoning degradation.'),
        ('p5', 'P5', 'Gupta (2025)', 'Placeholder Paper 5: Token-Level Perplexity Shifts Across Quantization Schemes', ['A. Gupta', 'J. Becker'], 2025, 13, 'Wikitext-103 & C4', 'Comparative evaluation of GPTQ, AWQ, and SmoothQuant', 'AWQ achieves 0.4 lower perplexity than GPTQ on outlier tokens', 'Evaluated only on 7B parameter scale.', 'Activation-aware scaling significantly preserves high-magnitude outlier activations compared to round-to-nearest.'),
        ('p6', 'P6', 'Morales (2025)', 'Placeholder Paper 6: Hardware-Aware Kernel Optimizations for 4-Bit KV-Cache', ['R. Morales', 'C. Silva'], 2025, 16, 'Throughput & Memory Profiling on RTX 4090 / A100', 'FP8/INT4 compressed KV-cache GPU kernels', '2.8x batch size expansion at 16k context', 'Noticeable needle-in-a-haystack recall loss below 4 bits.', 'Compressing KV cache to 4 bits enables 2.8x higher inference concurrency with minimal retention loss.')
    ]
    
    papers = []
    claims = []
    for i, p in enumerate(papers_data):
        pid, short_lbl, cit_lbl, title, authors, yr, pages, dset, meth, metric, limit, conc = p
        paper = schemas.PaperMetadata(
            paper_id=pid,
            short_label=short_lbl,
            citation_label=cit_lbl,
            palette_index=i,
            source=schemas.PaperSource.DEMO,
            arxiv_id=None,
            filename=f'{pid}_quantization_placeholder.pdf',
            title=title,
            authors=authors,
            year=yr,
            page_count=pages,
            sections_found=[schemas.SectionName.ABSTRACT, schemas.SectionName.METHODOLOGY, schemas.SectionName.RESULTS, schemas.SectionName.CONCLUSION],
            dataset=dset,
            sample_size=f'n={800 + i*400}',
            methodology=meth,
            primary_metric=metric,
            limitations=limit,
            core_conclusion=conc,
            extraction_model='meta-llama/Llama-3.1-8B-Instruct'
        )
        papers.append(paper)
        
        claim_defs = [
            (schemas.ClaimType.EMPIRICAL_RESULT, 'Benchmark Accuracy', f'{short_lbl} reports: {metric}.', metric, f'{pid}-c1', False, schemas.SectionName.RESULTS, 5, f'Empirical results establish that {title} yielded {metric}.'),
            (schemas.ClaimType.METHOD, 'Quantization Strategy', f'{short_lbl} applies {meth}.', None, f'{pid}-c2', False, schemas.SectionName.METHODOLOGY, 3, f'Our implementation details {meth} across all target evaluation checkpoints.'),
            (schemas.ClaimType.CONCLUSION, 'Deployment Recommendation', f'{short_lbl} concludes: {conc}', None, f'{pid}-c3', False, schemas.SectionName.CONCLUSION, pages - 1, f'In conclusion, our results demonstrate: {conc}'),
            (schemas.ClaimType.LIMITATION, 'Scope Boundary', f'{short_lbl} notes: {limit}', None, f'{pid}-c4', False, schemas.SectionName.LIMITATIONS, pages - 2, f'The primary limitation remains: {limit}'),
            (schemas.ClaimType.EMPIRICAL_RESULT, 'Secondary Metric', f'{short_lbl} evaluates auxiliary performance on {dset}.', 'Valid', f'{pid}-c5', pid in ['p3', 'p6'], schemas.SectionName.RESULTS, 7, f'Auxiliary assessment on {dset} verifies primary trends.')
        ]
        
        for ctype, topic, stmt, mval, cid, is_gap, sec, pg, quote in claim_defs:
            claims.append(schemas.ExtractedClaim(
                claim_id=cid,
                paper_id=pid,
                claim_type=ctype,
                topic_hint=topic,
                statement=stmt,
                metric_value=mval,
                cluster_id='cl-1' if 'Accuracy' in topic or 'Deployment' in topic else 'cl-2',
                is_research_gap=is_gap,
                provenance=schemas.Provenance(
                    paper_id=pid,
                    paper_title=title,
                    section=sec,
                    page_number=pg,
                    verbatim_quote=quote
                )
            ))

    def make_edge(src_cid, tgt_cid, rel, conf, sim, expl, cl_id):
        s_claim = next(c for c in claims if c.claim_id == src_cid)
        t_claim = next(c for c in claims if c.claim_id == tgt_cid)
        eid = f"e-{src_cid.replace('-', '')}-{tgt_cid.replace('-', '')}"
        return schemas.ClaimComparisonEdge(
            edge_id=eid,
            source_claim_id=src_cid,
            target_claim_id=tgt_cid,
            source=s_claim.provenance,
            target=t_claim.provenance,
            relation=rel,
            confidence=conf,
            cosine_similarity=sim,
            explanation=expl,
            cluster_id=cl_id,
            referee_model='meta-llama/Llama-3.1-8B-Instruct'
        )

    edges = [
        make_edge('p1-c1', 'p2-c1', schemas.RelationType.CONTRADICT, 0.94, 0.82, 'Zheng (2024) asserts 4-bit quantization loses only 0.8 points and is safe, while Okonkwo (2024) demonstrates a catastrophic 7.9 point drop at 32k context.', 'cl-1'),
        make_edge('p1-c3', 'p2-c3', schemas.RelationType.CONTRADICT, 0.91, 0.79, 'Zheng concludes 4-bit models preserve general reasoning, while Okonkwo warns long-context reasoning is severely compromised.', 'cl-1'),
        make_edge('p1-c4', 'p2-c4', schemas.RelationType.METHODOLOGY_DELTA, 0.95, 0.78, 'The discrepancy between Zheng and Okonkwo is explained by context boundary conditions: Zheng capped testing at 2k tokens while Okonkwo tested at 32k tokens.', 'cl-1'),
        make_edge('p2-c2', 'p5-c2', schemas.RelationType.AGREE, 0.89, 0.75, 'Both Okonkwo (2024) and Gupta (2025) find that activation-aware outlier protection (AWQ) is critical to preventing representational collapse in low-bit regimes.', 'cl-2'),
        make_edge('p1-c1', 'p4-c1', schemas.RelationType.AGREE, 0.86, 0.73, 'Schneider (2025) agrees with Zheng (2024) that 4-bit formats with adapter tuning preserve benchmark reasoning within 0.3-0.8% of full precision.', 'cl-1'),
        make_edge('p1-c2', 'p3-c2', schemas.RelationType.METHODOLOGY_DELTA, 0.88, 0.72, 'Zheng used standard Wikitext calibration, whereas Al-Mansoor proves that varying calibration sets alters perplexity by 1.4 points across domains.', 'cl-2'),
        make_edge('p2-c1', 'p6-c1', schemas.RelationType.METHODOLOGY_DELTA, 0.85, 0.69, 'Okonkwo quantizes model weights, while Morales quantizes the dynamic KV cache, offering complementary throughput advantages with different loss profiles.', 'cl-2'),
        make_edge('p4-c3', 'p5-c3', schemas.RelationType.AGREE, 0.83, 0.67, 'Both Schneider and Gupta agree that isolated high-precision elements prevent reasoning degradation.', 'cl-1')
    ]
    
    gaps = [
        schemas.ResearchGap(
            signal='RESEARCH_GAP',
            gap_id='gap-p3-c5',
            claim_id='p3-c5',
            paper_id='p3',
            statement='Al-Mansoor (2024) notes all calibration corpora were English-only; multilingual quantization behavior remains unbenchmarked across this entire paper group.',
            provenance=next(c.provenance for c in claims if c.claim_id == 'p3-c5'),
            best_match_similarity=0.41,
            reason='No other paper in this set evaluates non-English multilingual calibration sensitivity in 4-bit models.'
        ),
        schemas.ResearchGap(
            signal='RESEARCH_GAP',
            gap_id='gap-p6-c5',
            claim_id='p6-c5',
            paper_id='p6',
            statement='Morales (2025) benchmarks GPU memory throughput and batch expansion, but lacks needle-in-a-haystack retrieval evaluation on multi-document reasoning tasks.',
            provenance=next(c.provenance for c in claims if c.claim_id == 'p6-c5'),
            best_match_similarity=0.36,
            reason='No other paper in this set measures hardware kernel memory latency and KV-cache compression trade-offs.'
        )
    ]
    
    clusters = [
        schemas.TopicCluster(
            cluster_id='cl-1',
            label='Quantization Accuracy Trade-offs & Benchmark Parity',
            claim_ids=['p1-c1', 'p1-c3', 'p2-c1', 'p2-c3', 'p4-c1', 'p4-c3'],
            paper_ids=['p1', 'p2', 'p4'],
            mean_similarity=0.77
        ),
        schemas.TopicCluster(
            cluster_id='cl-2',
            label='Calibration Domain Shifts & KV-Cache Compression',
            claim_ids=['p2-c2', 'p3-c2', 'p5-c2', 'p6-c1'],
            paper_ids=['p2', 'p3', 'p5', 'p6'],
            mean_similarity=0.72
        )
    ]
    
    cross_pairs = 375
    candidate_pairs = 24
    referee_evaluated = 8
    pair_reduction = round(100 * (1 - candidate_pairs / cross_pairs), 1)
    
    consensus = schemas.ConsensusReport(
        consensus_score=56,
        executive_summary='Analysis of 6 LLM quantization papers reveals widespread consensus that 4-bit weight quantization preserves standard short-context benchmarks (MMLU, GSM8k) within 0.8 points of FP16. However, a major empirical conflict exists regarding long-context deployment: 4-bit models lose up to 7.9 points at 32k context on complex reasoning tasks (Okonkwo 2024). Calibration set diversity and activation outlier protection (AWQ) are critical mediators of accuracy.',
        agreed_findings=[
            'Short-context instruction following is well preserved in 4-bit weight-only quantization (Zheng 2024, Schneider 2025).',
            'Activation outlier protection (AWQ) prevents numerical collapse in low-bit representations (Okonkwo 2024, Gupta 2025).'
        ],
        top_contradictions=[
            schemas.TopContradiction(
                edge_id='e-p1c1-p2c1',
                headline='Deployment safety dispute: Zheng (2024) reports 4-bit models match FP16 within 0.8 points, but Okonkwo (2024) shows a 7.9-point drop at 32k context.'
            )
        ],
        gap_ids=['gap-p3-c5', 'gap-p6-c5'],
        recommended_next_steps=[
            'Standardize long-context (>16k) evaluations for all low-bit model releases.',
            'Benchmark multilingual calibration sets to avoid regional language degradation.',
            'Combine 4-bit weight compression with 4-bit KV cache kernels for end-to-end evaluation.'
        ]
    )
    
    stats = schemas.AnalysisStats(
        paper_count=6,
        claim_count=30,
        cross_paper_pairs_total=cross_pairs,
        candidate_pairs=candidate_pairs,
        referee_pairs_evaluated=referee_evaluated,
        referee_calls=2,
        pair_reduction_pct=pair_reduction,
        stage_latency_ms=schemas.StageLatency(
            ingestion_ms=750,
            extraction_ms=4800,
            embedding_ms=62,
            clustering_ms=11,
            referee_ms=1950,
            consensus_ms=1150,
            total_ms=8723
        )
    )
    
    res = schemas.AnalysisResult(
        schema_version='1.0.0',
        analysis_id='demo-llm_quantization',
        mode=schemas.AnalysisMode.DEMO,
        preset_id='llm_quantization',
        fixture_provenance=schemas.FixtureProvenance.SYNTHETIC_PLACEHOLDER,
        generated_at='2026-10-26T21:00:00Z',
        papers=papers,
        claims=claims,
        clusters=clusters,
        edges=edges,
        gaps=gaps,
        consensus=consensus,
        stats=stats,
        models=MODELS,
        warnings=['This dataset is synthetic placeholder data for hackathon development. Honest open-source disclosure.']
    )
    return res

def make_microgrids():
    papers_data = [
        ('p1', 'P1', 'Adeyemi (2024)', 'Placeholder Paper 1: Solar Microgrid Frequency Stability with Lithium Storage', ['S. Adeyemi', 'K. Adeleke'], 2024, 13, 'Southwest Nigeria Rural Grid Pilot (n=450 households)', 'Centralized LiFePO4 battery bank with droop control', 'Frequency fluctuation kept within +/- 0.15 Hz', 'High capital expenditure limits rural community adoption.', 'Lithium storage banks with droop-controlled inverters maintain grid frequency under sudden solar dropoffs.'),
        ('p2', 'P2', 'Nwosu (2024)', 'Placeholder Paper 2: Flow Battery Cycling Under Tropical Solar Irradiance', ['E. Nwosu', 'J. Becker'], 2024, 15, 'Tropical Climate Testbed (38C ambient avg)', 'Vanadium redox flow battery with passive convective cooling', 'Capacity retention of 98.4% over 1,200 deep cycles', 'Low energy density requires 3x physical footprint vs Lithium.', 'Vanadium flow batteries exhibit superior thermal resilience in tropical climates without active air conditioning.'),
        ('p3', 'P3', 'Hassan (2024)', 'Placeholder Paper 3: Decentralized Inverter Droop Control in Rural Grids', ['M. Hassan', 'A. Bello'], 2024, 12, '12-Node Distributed Microgrid Simulation & Field Trial', 'Decentralized peer-to-peer reactive power sharing', 'Voltage sag reduced by 34% at terminal feeder nodes', 'Communication latency spikes destabilize synchronization.', 'Decentralized droop control eliminates single points of failure in remote agricultural microgrids.'),
        ('p4', 'P4', 'Kiplagat (2025)', 'Placeholder Paper 4: Peak Shaving Economics in Off-Grid Agricultural Clusters', ['D. Kiplagat', 'F. Ochieng'], 2025, 14, 'Sub-Saharan Grain Milling Co-op Data (n=12 mini-grids)', 'Dynamic time-of-use tariff scheduling with automated demand response', '31% Reduction in evening peak generator fuel consumption', 'Requires smart meters and reliable mobile GSM data coverage.', 'Automated demand response significantly lowers reliance on backup diesel generation during low solar hours.'),
        ('p5', 'P5', 'Mensah (2025)', 'Placeholder Paper 5: Predictive Dispatch Algorithms for High-Variability Loads', ['K. Mensah', 'B. Mensah'], 2025, 16, 'West African Monsoon Solar Farm Dataset', 'LSTM neural network forecasting paired with mixed-integer linear programming', '19% Improvement in battery state-of-charge reserve margins', 'Computational latency requires cloud connectivity or edge TPU.', 'Short-horizon cloud prediction enables preemptive battery charging before monsoon cloud cover arrival.'),
        ('p6', 'P6', 'Diop (2025)', 'Placeholder Paper 6: Thermal Degradation Mitigation in Distributed Battery Banks', ['M. Diop', 'L. Sow'], 2025, 11, 'Sahelian Environmental Chamber Stress Test (45C peak)', 'Phase-change material (PCM) passive thermal envelopes', 'Cell temperature rise constrained to 6.2C during peak discharge', 'PCM materials add 15% to battery pack initial weight.', 'Passive phase-change cooling extends battery lifespan in arid desert zones without parasitic electrical load.')
    ]
    
    papers = []
    claims = []
    for i, p in enumerate(papers_data):
        pid, short_lbl, cit_lbl, title, authors, yr, pages, dset, meth, metric, limit, conc = p
        paper = schemas.PaperMetadata(
            paper_id=pid,
            short_label=short_lbl,
            citation_label=cit_lbl,
            palette_index=i,
            source=schemas.PaperSource.DEMO,
            arxiv_id=None,
            filename=f'{pid}_microgrids_placeholder.pdf',
            title=title,
            authors=authors,
            year=yr,
            page_count=pages,
            sections_found=[schemas.SectionName.ABSTRACT, schemas.SectionName.METHODOLOGY, schemas.SectionName.RESULTS, schemas.SectionName.CONCLUSION],
            dataset=dset,
            sample_size=f'n={500 + i*300}',
            methodology=meth,
            primary_metric=metric,
            limitations=limit,
            core_conclusion=conc,
            extraction_model='meta-llama/Llama-3.1-8B-Instruct'
        )
        papers.append(paper)
        
        claim_defs = [
            (schemas.ClaimType.EMPIRICAL_RESULT, 'Grid Stability & Metrics', f'{short_lbl} achieves {metric}.', metric, f'{pid}-c1', False, schemas.SectionName.RESULTS, 5, f'Field measurements verify that {title} yielded {metric}.'),
            (schemas.ClaimType.METHOD, 'Control Architecture', f'{short_lbl} implements {meth}.', None, f'{pid}-c2', False, schemas.SectionName.METHODOLOGY, 3, f'Our design incorporates {meth} to ensure stable operating conditions.'),
            (schemas.ClaimType.CONCLUSION, 'Core Recommendation', f'{short_lbl} concludes: {conc}', None, f'{pid}-c3', False, schemas.SectionName.CONCLUSION, pages - 1, f'In conclusion, our research indicates: {conc}'),
            (schemas.ClaimType.LIMITATION, 'Operational Barrier', f'{short_lbl} identifies limitation: {limit}', None, f'{pid}-c4', False, schemas.SectionName.LIMITATIONS, pages - 2, f'A significant deployment hurdle remains: {limit}'),
            (schemas.ClaimType.EMPIRICAL_RESULT, 'Field Validation', f'{short_lbl} verifies operational metrics under {dset}.', 'Valid', f'{pid}-c5', pid in ['p2', 'p6'], schemas.SectionName.RESULTS, 6, f'Auxiliary field tests confirm performance under {dset}.')
        ]
        
        for ctype, topic, stmt, mval, cid, is_gap, sec, pg, quote in claim_defs:
            claims.append(schemas.ExtractedClaim(
                claim_id=cid,
                paper_id=pid,
                claim_type=ctype,
                topic_hint=topic,
                statement=stmt,
                metric_value=mval,
                cluster_id='cl-1' if 'Stability' in topic or 'Recommendation' in topic else 'cl-2',
                is_research_gap=is_gap,
                provenance=schemas.Provenance(
                    paper_id=pid,
                    paper_title=title,
                    section=sec,
                    page_number=pg,
                    verbatim_quote=quote
                )
            ))

    def make_edge(src_cid, tgt_cid, rel, conf, sim, expl, cl_id):
        s_claim = next(c for c in claims if c.claim_id == src_cid)
        t_claim = next(c for c in claims if c.claim_id == tgt_cid)
        eid = f"e-{src_cid.replace('-', '')}-{tgt_cid.replace('-', '')}"
        return schemas.ClaimComparisonEdge(
            edge_id=eid,
            source_claim_id=src_cid,
            target_claim_id=tgt_cid,
            source=s_claim.provenance,
            target=t_claim.provenance,
            relation=rel,
            confidence=conf,
            cosine_similarity=sim,
            explanation=expl,
            cluster_id=cl_id,
            referee_model='meta-llama/Llama-3.1-8B-Instruct'
        )

    edges = [
        make_edge('p1-c3', 'p2-c3', schemas.RelationType.CONTRADICT, 0.88, 0.79, 'Adeyemi (2024) advocates centralized lithium storage for frequency stability, whereas Nwosu (2024) argues flow batteries are far superior in tropical heat due to lithium thermal degradation.', 'cl-1'),
        make_edge('p1-c2', 'p3-c2', schemas.RelationType.CONTRADICT, 0.91, 0.76, 'Adeyemi relies on a centralized master storage bank, whereas Hassan proves decentralized peer-to-peer droop control is superior for avoiding single points of failure.', 'cl-2'),
        make_edge('p1-c1', 'p3-c1', schemas.RelationType.AGREE, 0.89, 0.74, 'Both Adeyemi (2024) and Hassan (2024) confirm that droop-controlled inverter logic maintains terminal feeder voltage and frequency within allowable bounds.', 'cl-1'),
        make_edge('p4-c3', 'p5-c3', schemas.RelationType.AGREE, 0.87, 0.72, 'Both Kiplagat (2025) and Mensah (2025) find that predictive scheduling algorithms reduce backup diesel fuel consumption by 19-31%.', 'cl-1'),
        make_edge('p2-c1', 'p6-c1', schemas.RelationType.METHODOLOGY_DELTA, 0.86, 0.73, 'Nwosu solves tropical battery degradation by switching chemistry to vanadium flow, whereas Diop retains lithium chemistry but wraps packs in phase-change material.', 'cl-2'),
        make_edge('p3-c1', 'p4-c1', schemas.RelationType.METHODOLOGY_DELTA, 0.84, 0.70, 'Hassan achieves grid stability through electrical droop control (voltage sag -34%), whereas Kiplagat achieves stability through behavioral economics and time-of-use tariffs.', 'cl-1'),
        make_edge('p1-c4', 'p6-c4', schemas.RelationType.METHODOLOGY_DELTA, 0.85, 0.68, 'Adeyemi highlights the high cost of active air conditioning for lithium banks, whereas Diop demonstrates zero-power passive phase-change envelopes.', 'cl-2'),
        make_edge('p4-c4', 'p5-c4', schemas.RelationType.AGREE, 0.83, 0.67, 'Both Kiplagat and Mensah acknowledge that advanced scheduling algorithms depend heavily on reliable telecommunications and local edge compute.', 'cl-2')
    ]
    
    gaps = [
        schemas.ResearchGap(
            signal='RESEARCH_GAP',
            gap_id='gap-p2-c5',
            claim_id='p2-c5',
            paper_id='p2',
            statement='Nwosu (2024) evaluates vanadium electrolyte supply chain costs and recycling logistics, a chemical lifecycle dimension unaddressed by other papers.',
            provenance=next(c.provenance for c in claims if c.claim_id == 'p2-c5'),
            best_match_similarity=0.40,
            reason='No other paper in this set evaluates vanadium chemical electrolyte sourcing and end-of-life recycling.'
        ),
        schemas.ResearchGap(
            signal='RESEARCH_GAP',
            gap_id='gap-p6-c5',
            claim_id='p6-c5',
            paper_id='p6',
            statement='Diop (2025) benchmarks physical phase-change material weight penalty on mobile transportable power units in Sahelian conditions.',
            provenance=next(c.provenance for c in claims if c.claim_id == 'p6-c5'),
            best_match_similarity=0.37,
            reason='No other paper in this set evaluates physical thermal material weights and containerized transport logistics.'
        )
    ]
    
    clusters = [
        schemas.TopicCluster(
            cluster_id='cl-1',
            label='Microgrid Frequency Stability & Economic Dispatch',
            claim_ids=['p1-c1', 'p1-c3', 'p3-c1', 'p4-c1', 'p4-c3', 'p5-c3'],
            paper_ids=['p1', 'p3', 'p4', 'p5'],
            mean_similarity=0.75
        ),
        schemas.TopicCluster(
            cluster_id='cl-2',
            label='Tropical Thermal Resilience & Chemistry Alternatives',
            claim_ids=['p2-c1', 'p2-c3', 'p6-c1', 'p6-c3'],
            paper_ids=['p2', 'p6'],
            mean_similarity=0.71
        )
    ]
    
    cross_pairs = 375
    candidate_pairs = 24
    referee_evaluated = 8
    pair_reduction = round(100 * (1 - candidate_pairs / cross_pairs), 1)
    
    consensus = schemas.ConsensusReport(
        consensus_score=56,
        executive_summary='Synthesis of 6 solar microgrid research papers demonstrates strong agreement that predictive demand scheduling and droop inverter control prevent brownouts during sudden solar irradiance dropoffs. However, a sharp technological conflict divides battery storage strategies: centralized lithium banks offer superior frequency stabilization (Adeyemi 2024), but suffer rapid thermal degradation in tropical ambient heat (>38C), where vanadium flow batteries and passive phase-change cooling envelopes provide dramatically higher cycling longevity (Nwosu 2024, Diop 2025).',
        agreed_findings=[
            'Inverter droop control stabilizes feeder voltage and frequency across remote off-grid nodes (Adeyemi 2024, Hassan 2024).',
            'Predictive load dispatch reduces reliance on backup fossil generators by up to 31% (Kiplagat 2025, Mensah 2025).'
        ],
        top_contradictions=[
            schemas.TopContradiction(
                edge_id='e-p1c3-p2c3',
                headline='Storage chemistry controversy: Adeyemi (2024) favors lithium for frequency control, while Nwosu (2024) shows flow batteries prevent tropical thermal decay.'
            )
        ],
        gap_ids=['gap-p2-c5', 'gap-p6-c5'],
        recommended_next_steps=[
            'Field-test hybrid lithium-flow storage architectures to capture both fast frequency response and thermal longevity.',
            'Integrate passive phase-change thermal barriers directly into rural battery casing standards.',
            'Develop offline edge dispatch heuristics that do not require cellular GSM connectivity.'
        ]
    )
    
    stats = schemas.AnalysisStats(
        paper_count=6,
        claim_count=30,
        cross_paper_pairs_total=cross_pairs,
        candidate_pairs=candidate_pairs,
        referee_pairs_evaluated=referee_evaluated,
        referee_calls=2,
        pair_reduction_pct=pair_reduction,
        stage_latency_ms=schemas.StageLatency(
            ingestion_ms=710,
            extraction_ms=4650,
            embedding_ms=59,
            clustering_ms=10,
            referee_ms=1900,
            consensus_ms=1180,
            total_ms=8509
        )
    )
    
    res = schemas.AnalysisResult(
        schema_version='1.0.0',
        analysis_id='demo-microgrids',
        mode=schemas.AnalysisMode.DEMO,
        preset_id='microgrids',
        fixture_provenance=schemas.FixtureProvenance.SYNTHETIC_PLACEHOLDER,
        generated_at='2026-10-26T21:00:00Z',
        papers=papers,
        claims=claims,
        clusters=clusters,
        edges=edges,
        gaps=gaps,
        consensus=consensus,
        stats=stats,
        models=MODELS,
        warnings=['This dataset is synthetic placeholder data for hackathon development. Honest open-source disclosure.']
    )
    return res

if __name__ == '__main__':
    r1 = make_radiology()
    p1 = OUT_DIR / 'demo_radiology_8papers.json'
    p1.write_text(json.dumps(r1.model_dump(mode='json'), indent=2), encoding='utf-8')
    print(f'Generated {p1.name} with {len(r1.papers)} papers, {len(r1.claims)} claims, {len(r1.edges)} edges.')
    
    r2 = make_llm_quant()
    p2 = OUT_DIR / 'demo_llm_quantization_6papers.json'
    p2.write_text(json.dumps(r2.model_dump(mode='json'), indent=2), encoding='utf-8')
    print(f'Generated {p2.name} with {len(r2.papers)} papers, {len(r2.claims)} claims, {len(r2.edges)} edges.')
    
    r3 = make_microgrids()
    p3 = OUT_DIR / 'demo_microgrids_6papers.json'
    p3.write_text(json.dumps(r3.model_dump(mode='json'), indent=2), encoding='utf-8')
    print(f'Generated {p3.name} with {len(r3.papers)} papers, {len(r3.claims)} claims, {len(r3.edges)} edges.')
    
    print('All 3 placeholder fixtures generated successfully and validated against Pydantic schema!')
