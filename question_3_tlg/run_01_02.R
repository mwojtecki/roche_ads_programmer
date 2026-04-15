# To capture all log please run below script
system("Rscript question_3_tlg/01_create_ae_summary_table.R > question_3_tlg/summary_table_log.txt 2>&1")
system("Rscript question_3_tlg/02_create_visualizations.R > question_3_tlg/visualizations_log.txt 2>&1")