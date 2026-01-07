library(here)
library(dplyr)
library(tidyr)
library(ggplot2)
library(readr)
library(scales)
library(ggrepel)
library(purrr)
library(patchwork)
library(grid)
# ========== Effect Size Function ==========
calculate_rank_biserial <- function(wilcox_statistic, n) {
  total_rank_sum <- n * (n + 1) / 2
  r <- 1 - (2 * wilcox_statistic / total_rank_sum)
  return(r)
}

datasets <- c("bugsinpy", "defects4j")
models <- c("codellama_7b_instruct_fp16_Instruction", "deepseek_coder_6.7b_instruct_fp16_Instruction", "deepseek_coder_v2_16b_lite_instruct_fp16_Instruction")

name_map <- c(
  "bugsinpy" = "bpy",
  "defects4j" = "d4j",
  
  "codellama_7b_instruct_fp16_Instruction" = "cl_inst",
  "deepseek_coder_6.7b_instruct_fp16_Instruction" = "dsc_inst",
  "deepseek_coder_v2_16b_lite_instruct_fp16_Instruction" = "dsc2_inst"
)
# Helper to abbreviate using name_map
shorten_name <- function(x) {
  ifelse(x %in% names(name_map), name_map[x], x)
}
# print(shorten_name("codellama_7b_instruct_fp16_Instruction"))


# ================================ RQ1.1: statistical test on baseline and individual heuristics (n=10) ================================
# ================================ RQ1.2: statistical test on baseline and HAFix-Agg (n=70) ================================
# ================================ RQ2.1: statistical test on baseline of 3 prompt styles ================================
# ================================ RQ2.2: statistical test on HAFix-Agg of 3 prompt styles ================================
statistical_test_passk_heuristics <- function(input_file_path) {
  df <- read_csv(input_file_path, show_col_types = FALSE)
  
  # Convert percentages to numeric
  df_clean <- df %>%
    mutate(across(starts_with("setting_"), ~ as.numeric(gsub("%", "", .)) / 100))
  # print(df_clean)
  
  # Add row identifier from the first column `pass@k`
  df_clean$pass_k <- df[[1]]
  
  # ==== Friedman Test ====
  friedman_matrix <- df_clean %>% select(starts_with("setting_")) %>% as.matrix()
  cat("\n=== Friedman Test Across All Settings ===\n")
  print(friedman.test(friedman_matrix))
  
  # Pivot to long format
  df_long <- df_clean %>%
    pivot_longer(cols = starts_with("setting_"), names_to = "setting", values_to = "value")
  # print(df_long)
  
  pw_test <- pairwise.wilcox.test(
    x = df_long$value,
    g = df_long$setting,
    paired = TRUE,
    p.adjust.method = "none"
  )
  print(pw_test)
  
  # Prepare setting-wise list of vectors
  setting_passk_list <- df_clean %>%
    select(starts_with("setting_")) %>%
    as.list()
  
  setting_names <- names(setting_passk_list)
  
  # If setting_1 exists, do baseline-vs-others only
  if ("setting_1" %in% setting_names) {
    cat("\n=== Baseline (setting_1) vs Other Settings: Wilcoxon Test + Effect Size ===\n")
    baseline <- setting_passk_list[["setting_1"]]
    n <- length(baseline)
    
    for (setting_id in setting_names) {
      if (setting_id == "setting_1") next
      
      other <- setting_passk_list[[setting_id]]
      test <- wilcox.test(baseline, other, paired = TRUE)
      w_stat <- as.numeric(test$statistic)
      r <- calculate_rank_biserial(w_stat, n)
      
      cat(setting_id,
          sprintf("%.4f", test$p.value),
          sprintf("%.2f", r),
          sep = ",", fill = TRUE)
    }
  } else {
    # setting_1 not present → do all pairwise comparisons with effect size
    cat("\n=== All Pairwise Wilcoxon Tests + Effect Sizes ===\n")
    for (i in 1:(length(setting_names) - 1)) {
      for (j in (i + 1):length(setting_names)) {
        setting_i <- setting_names[i]
        setting_j <- setting_names[j]
        
        vec_i <- setting_passk_list[[setting_i]]
        vec_j <- setting_passk_list[[setting_j]]
        
        test <- wilcox.test(vec_i, vec_j, paired = TRUE)
        w_stat <- as.numeric(test$statistic)
        n <- length(vec_i)
        r <- calculate_rank_biserial(w_stat, n)
        cat(paste0(setting_i, " vs ", setting_j, ":"),
            test$p.value,
            sprintf("r=%.2f", r), sep = ",", fill = TRUE)
      }
    }
  }
}

# Verify current working directory
getwd()
# Config
base_dir <- "RQ1_2"
models_short <- c("codellama_7b", "deepseek_coder_6.7b", "deepseek_coder_v2")
# datasets <- c("bugsinpy")
# models <- c(
#   "codellama_7b_instruct_fp16_Instruction"
# )
# Loop over all combinations
for (dataset in datasets) {
  cat("\n========================", dataset, "========================\n")
  # for (model_name in models) {
  #   cat("\n========================", dataset, model_name, "========================\n")
  #   # 1. For individual heuristics
  #   input_file_path_1 <- file.path(base_dir, dataset, model_name, "hafix_pass_at_k.csv")
  #   statistical_test_passk_heuristics(input_file_path_1)
  #   # 2.1 For Baseline and HAFix-Agg of each model
  #   # input_file_path_2 <- file.path(base_dir, dataset, model_name, "hafix_pass_at_k_70.csv")
  #   # statistical_test_passk_heuristics(input_file_path_2)
  # }
  # # 2.2 For Baseline and HAFix-Agg of all models
  # input_file_path_22 <- file.path(base_dir, dataset, "baseline_hafix_pass_at_k_70_all_models.csv")
  # statistical_test_passk_heuristics(input_file_path_22)
  
  # 3. Baseline on different prompt styles
  for (model_name_short in models_short) {
    cat("\n========================", dataset, model_name_short, "========================\n")
    input_file_path_3 <- file.path(base_dir, dataset, paste0("baseline_prompt_styles_pass_at_k_", model_name_short, ".csv"))
    statistical_test_passk_heuristics(input_file_path_3)
    # 4. HAFix-Agg on different prompt styles
    # input_file_path_4 <- file.path(base_dir, dataset, paste0("hafix_prompt_styles_pass_at_k_", model_name_short, ".csv"))
    # statistical_test_passk_heuristics(input_file_path_4)
  }
}





# =================================== RQ3: 1.1 Inference token and time: box plot of different bugs across different scenarios ===================================
box_plot_cost_of_bugs_across_scenarios <- function(dataset, model_name, base_dir, file_prefix, value_column, y_label, file_tag,
                                                   ylim = NULL, ybreak = NULL, font_size = 12) {
  input_dir <- file.path(base_dir, dataset, model_name)
  output_dir <- input_dir
  
  scenario_files <- list(
    Exhaustive = paste0(file_prefix, "_exhaustive.csv"),
    Early_stop = paste0(file_prefix, "_early_stop.csv"),
    Sort_accuracy = paste0(file_prefix, "_es_accsorted.csv"),
    Sort_unique = paste0(file_prefix, "_es_unisorted.csv")
  )
  
  custom_cost_labels <- c(
    Exhaustive = "Exhaustive",
    Early_stop = "ES",
    Sort_accuracy = "ES-AccSorted",
    Sort_unique = "ES-UniSorted"
  )
  
  summary_list <- lapply(names(scenario_files), function(scenario_name) {
    file_path <- file.path(input_dir, scenario_files[[scenario_name]])
    df <- read_csv(file_path, show_col_types = FALSE)
    
    df %>%
      group_by(bug_id) %>%
      summarize(total_value = sum(.data[[value_column]]), .groups = "drop") %>%
      rename(!!scenario_name := total_value)
  })
  
  df_summary <- Reduce(function(x, y) full_join(x, y, by = "bug_id"), summary_list)
  df_summary_long <- df_summary %>%
    pivot_longer(cols = -bug_id, names_to = "type", values_to = "value")
  
  # ==== Median Percentage Reductions ====
  medians <- df_summary %>%
    summarise(across(everything(), median, na.rm = TRUE))
  
  exhaustive_median <- medians$Exhaustive
  reduction_es <- 100 * (exhaustive_median - medians$Early_stop) / exhaustive_median
  reduction_accsorted <- 100 * (exhaustive_median - medians$Sort_accuracy) / exhaustive_median
  reduction_unisorted <- 100 * (exhaustive_median - medians$Sort_unique) / exhaustive_median
  overall_avg <- mean(c(reduction_es, reduction_accsorted, reduction_unisorted), na.rm = TRUE)
  
  cat(sprintf("\n==== Median Reductions for %s on %s ====\n", dataset, model_name))
  cat(sprintf("ES: %.2f%% | ES-AccSorted: %.2f%% | ES-UniSorted: %.2f%% | average: %.2f%%\n",
              reduction_es, reduction_accsorted, reduction_unisorted, overall_avg))
  
  # ==== Friedman Test ====
  cat("\n==== Friedman Test: ", file_tag, " ====\n")
  friedman_res <- friedman.test(as.matrix(df_summary[,-1]))
  print(friedman_res)
  
  # ==== Post-hoc Wilcoxon Signed-Rank Test (paired, two-sided) with Bonferroni correction ====
  cat("\n==== Post-hoc Wilcoxon Tests ====\n")
  pairwise_res <- pairwise.wilcox.test(
    x = df_summary_long$value,
    g = df_summary_long$type,
    paired = TRUE,
    p.adjust.method = "none"
  )
  print(pairwise_res)
  
  # ==== Effect Size for All Pairs ====
  cat("\n==== Effect Sizes for All Pairs (version 2: wilcox.test + rank-biserial) ====\n")
  scenarios <- colnames(df_summary)[-1]
  n <- nrow(df_summary)
  
  combn(scenarios, 2, simplify = FALSE) %>%
    walk(function(pair) {
      a <- df_summary[[pair[1]]]
      b <- df_summary[[pair[2]]]
      
      test <- wilcox.test(a, b, paired = TRUE)
      # w_stat <- as.numeric(test$statistic)
      r <- calculate_rank_biserial(test$statistic, n)
      
      cat(sprintf("%s vs %s: p = %.4f | r (rank-biserial) = %.2f\n",
                  pair[1], pair[2], test$p.value, r))
    })
  
  df_summary_long$type <- factor(df_summary_long$type, levels = c(
    "Exhaustive", "Early_stop", "Sort_accuracy", "Sort_unique"
  ))
  plot <- ggplot(df_summary_long, aes(x = type, y = value)) +
    geom_boxplot(outlier.size = 0.5, width = 0.6, fill = "white", color = "black") +
    stat_summary(
      fun = median,
      geom = "text",
      aes(label = comma_format(accuracy = 1)(..y..)),
      vjust = -0.7,
      size = font_size * 0.26,
      color = "black"
    ) +
    labs(x = "Cost Scenarios", y = y_label) +
    scale_x_discrete(labels = custom_cost_labels) +
    scale_y_continuous(labels = comma_format(accuracy = 1)) +
    theme_bw(base_size = font_size) +
    theme(
      panel.border = element_rect(color = "black", fill = NA, size = 0.8),
      axis.text.x = element_text(angle = 30, hjust = 1, size = font_size - 2),
      axis.text.y = element_text(size = font_size - 2),
      axis.title.x = element_text(size = font_size),
      axis.title.y = element_text(size = font_size, margin = margin(r = 10)),
      plot.margin = margin(10, 10, 10, 10)
    )
  # Add limits and breaks only if needed
  if (!is.null(ylim)) {
    plot <- plot + coord_cartesian(ylim = c(0, ylim))
    
    if (!is.null(ybreak)) {
      plot <- plot + scale_y_continuous(
        labels = comma_format(accuracy = 1),
        breaks = seq(0, ylim, by = ybreak)
      )
    }
  }
  print(plot)
  
  output_filename <- paste0("rq3_box_plot_", file_tag, "_", shorten_name(dataset), "_", shorten_name(model_name), ".png")
  ggsave(
    filename = output_filename,
    plot = plot,
    path = output_dir,
    width = 7,
    height = 4.5,
    dpi = 600,
    units = "in"
  )
  return(overall_avg)
}

# Verify current working directory
getwd()
# Config
base_dir <- "RQ3"
all_reductions <- c()
# Loop over all combinations
for (dataset in datasets) {
  cat("\n========================", dataset, "========================\n")
  for (model_name in models) {
    cat("\n========================", dataset, model_name, "========================\n")
    
    # Token plot
    y_lim <- 500000
    y_break <- 100000
    ave_median <- box_plot_cost_of_bugs_across_scenarios(
      dataset = dataset,
      model_name = model_name,
      base_dir = base_dir,
      file_prefix = "token",
      value_column = "total_length",
      y_label = "Token Count per Bug",
      file_tag = "token",
      ylim = y_lim,
      ybreak = y_break,
      font_size = 17
    )
    
    # # Inference time plot
    # if (model_name == "deepseek_coder_6.7b_instruct_fp16_Instruction") {
    #   y_lim <- 1000
    #   y_break <- 250
    # } else {
    #   y_lim <- NULL
    #   y_break <- NULL
    # }
    # ave_median <- box_plot_cost_of_bugs_across_scenarios(
    #   dataset = dataset,
    #   model_name = model_name,
    #   base_dir = base_dir,
    #   file_prefix = "time",
    #   value_column = "duration_second",
    #   y_label = "Inference Time per Bug (s)",
    #   file_tag = "time",
    #   ylim = y_lim,
    #   ybreak = y_break,
    #   font_size = 17
    # )
    
    all_reductions <- c(all_reductions, ave_median)
  }
}
final_average <- mean(all_reductions, na.rm = TRUE)
cat(sprintf("\nFinal average reduction across all configurations: %.0f%%\n", final_average))




# =====================================RQ3: 2.1 Inference time: box plot of different bugs across different settings only in Exhaustive scenario=====================================
box_plot_exhaustive_time_by_setting <- function(dataset, model_name, base_dir, ylim = NULL, ybreak = NULL, font_size = 12) {
  # Define input/output paths
  input_dir <- file.path(base_dir, dataset, model_name)
  output_dir <- input_dir
  input_file <- file.path(input_dir, "time_exhaustive.csv")
  
  # Read CSV
  df <- read_csv(input_file, show_col_types = FALSE)
  
  # Define label mapping for settings
  setting_labels <- c(
    "1" = "Baseline",
    "2" = "CFN-modified",
    "3" = "CFN-all",
    "4" = "FN-modified",
    "5" = "FN-all",
    "6" = "FLN-all",
    "7" = "FN-pair",
    "8" = "FL-diff"
  )
  
  # Prepare data
  df_clean <- df %>%
    mutate(setting = setting_labels[as.character(setting_id)]) %>%
    # Set factor levels to match the order in setting_labels
    mutate(setting = factor(setting, levels = setting_labels)) %>%
    select(bug_id, setting, duration_second) %>%
    drop_na(duration_second) %>%
    filter(is.finite(duration_second))
  
  # Reshape for Friedman test (wide format by bug_id)
  df_wide <- df_clean %>%
    pivot_wider(names_from = setting, values_from = duration_second, id_cols = bug_id) %>%
    arrange(bug_id)
  # Convert columns (except bug_id) to numeric
  df_wide[ , -1] <- lapply(df_wide[ , -1], as.numeric)
  
  # ==== Friedman Test ====
  cat("\n==== Friedman Test: Inference Time across Settings (Exhaustive) ====\n")
  friedman_res <- friedman.test(as.matrix(df_wide[,-1]))
  print(friedman_res)
  
  # ==== Post-hoc Wilcoxon Test ====
  cat("\n==== Post-hoc Wilcoxon Tests (Bonferroni adjusted) ====\n")
  df_long <- df_clean %>%
    mutate(setting = factor(setting, levels = setting_labels))  # ensure factor order
  pairwise_res <- pairwise.wilcox.test(
    x = df_long$duration_second,
    g = df_long$setting,
    paired = TRUE,
    p.adjust.method = "none"
  )
  print(pairwise_res)
  
  cat("\n==== Effect Sizes for All Pairs (Wilcoxon + rank-biserial) ====\n")
  settings <- colnames(df_wide)[-1]
  n <- nrow(df_wide)
  
  combn(settings, 2, simplify = FALSE) %>%
    walk(function(pair) {
      a <- df_wide[[pair[1]]]
      b <- df_wide[[pair[2]]]
      test <- wilcox.test(a, b, paired = TRUE)
      r <- calculate_rank_biserial(test$statistic, n)
      cat(sprintf("%s vs %s: p = %.4g | r (rank-biserial) = %.2f\n",
                  pair[1], pair[2], test$p.value, r))
    })
  
  
  # Plot
  plot <- ggplot(df_clean, aes(x = setting, y = duration_second)) +
    geom_boxplot(outlier.size = 0.5, width = 0.6, fill = "white", color = "black") +
    stat_summary(
      fun = median,
      geom = "text",
      aes(label = comma_format(accuracy = 1)(..y..)),
      vjust = -0.7,
      size = font_size * 0.26,
      color = "black"
    ) +
    labs(x = "HAFix Heuristics", y = "Inference Time (Seconds)") +
    scale_y_continuous(labels = scales::comma) +
    theme_bw(base_size = font_size) +
    theme(
      panel.border = element_rect(color = "black", fill = NA, size = 0.8),
      axis.text.x = element_text(angle = 45, hjust = 1, size = font_size - 2),
      axis.text.y = element_text(size = font_size - 2),
      axis.title.x = element_text(size = font_size),
      axis.title.y = element_text(size = font_size, margin = margin(r = 10)),
      plot.margin = margin(10, 10, 10, 10)
    )
  # Add limits and breaks only if needed
  if (!is.null(ylim)) {
    plot <- plot + coord_cartesian(ylim = c(0, ylim))
    
    if (!is.null(ybreak)) {
      plot <- plot + scale_y_continuous(
        labels = comma_format(accuracy = 1),
        breaks = seq(0, ylim, by = ybreak)
      )
    }
  }
  
  # Save plot
  output_filename <- paste0("rq3_box_plot_time_exhaustive_by_setting_", shorten_name(dataset), "_", shorten_name(model_name), ".png")
  ggsave(
    filename = output_filename,
    plot = plot,
    path = output_dir,
    width = 7,
    height = 4.5,
    dpi = 600,
    units = "in"
  )
  return(plot)
}

# Verify current working directory
getwd()
# Config
base_dir <- "RQ3"
# Loop over all combinations
for (dataset in datasets) {
  cat("\n========================", dataset, "========================\n")
  for (model_name in models) {
    cat("\n========================", dataset, model_name, "========================\n")
    y_lim <- 300
    y_break <- 50
    f <- box_plot_exhaustive_time_by_setting(dataset, model_name, base_dir, ylim = y_lim, ybreak = y_break, font_size = 17)
    print(f)
  }
}




# ===================================RQ3: 3.1 Inference token: symmetric grouped bar chart, split to 4 subfigures===================================
plot_inference_token_symmetry <- function(dataset, model_name, base_dir, file_tag, input_file_name,
                                          font_size = 12, legend_enabled = TRUE,
                                          legend_output_path = NULL, legend_output_width = 6,
                                          legend_output_height = 1.5) {
  # Paths
  input_path <- file.path(base_dir, dataset, model_name, input_file_name)
  output_dir <- file.path(base_dir, dataset, model_name)
  output_filename <- paste0("rq3_symmetry_bar_setting_", file_tag, "_", shorten_name(dataset), "_", shorten_name(model_name), ".png")
  
  # Read and prepare data
  data <- read_csv(input_path, show_col_types = FALSE)
  colnames(data) <- c("type", "setting_id", "token_fixed", "token_not_fixed", "num_bugs_solved_newly")
  data$setting <- paste0("setting_", data$setting_id)
  data$bugs_append <- paste0("+", data$num_bugs_solved_newly)
  
  # Custom labels and colors
  custom_labeller <- as_labeller(c(
    "exhaustive" = "(1). Exhaustive",
    "early_stop" = "(2). ES",
    "es_accsorted" = "(3). ES-AccSorted",
    "es_unisorted" = "(4). ES-UniSorted"
  ))
  
  custom_heuristics_labels <- c(
    "setting_1" = "Baseline",
    "setting_2" = "CFN-modified",
    "setting_3" = "CFN-all",
    "setting_4" = "FN-modified",
    "setting_5" = "FN-all",
    "setting_6" = "FLN-all",
    "setting_7" = "FN-pair",
    "setting_8" = "FL-diff"
  )
  
  custom_colors <- c(
    "setting_6" = "#FDB462", "setting_3" = "#BEBADA", "setting_1" = "#8DD3C7", "setting_2" = "#FFFFB3",
    "setting_5" = "#80B1D3", "setting_4" = "#FB8072", "setting_7" = "#B3DE69", "setting_8" = "#FCCDE5"
  )
  data$setting <- factor(data$setting, levels = names(custom_heuristics_labels))
  
  # y-axis bounds
  y_min <- min(-data$token_not_fixed, na.rm = TRUE)
  y_max <- max(data$token_fixed, na.rm = TRUE)
  y_padding <- 0.15 * (y_max - y_min)
  text_position <- y_max + y_padding / 2
  
  # Plot group function
  plot_group <- function(df_group, y_label = FALSE, show_legend = legend_enabled) {
    # Local setting order per type
    local_setting_order <- unique(df_group$setting)
    
    label_text_size <- font_size * 0.29
    strip_text_size <- font_size + 3
    legend_text_size <- font_size + 3
    
    ggplot(df_group, aes(x = factor(setting, levels = local_setting_order), fill = setting)) +
      geom_bar(aes(y = token_fixed), stat = "identity", color = "black", alpha = 0.7) +
      geom_bar(aes(y = -token_not_fixed), stat = "identity", color = "black", alpha = 0.7) +
      geom_text(aes(y = text_position, label = bugs_append), vjust = -0.5, size = label_text_size, color = "blue") +
      facet_wrap(. ~ type, labeller = custom_labeller, switch = "x", scales = "free_x") +
      scale_y_continuous(
        labels = scales::comma_format(),
        limits = c(y_min - 0.3 * y_padding, y_max + 1.2 * y_padding)  # Increased upper limit
      ) +
      scale_fill_manual(values = custom_colors, labels = custom_heuristics_labels, name = NULL) +
      labs(
        x = NULL,
        y = if (y_label) "Inference Token Count\n   \u2190 F         S \u2192" else NULL
      ) +
      theme_minimal(base_size = font_size) +
      theme(
        axis.text.x = element_blank(),
        strip.text = element_text(size = strip_text_size),
        axis.title.y = element_text(size = font_size, margin = margin(r = 12)),
        legend.text = element_text(size = legend_text_size),
        legend.position = if (show_legend) "right" else "none",
        plot.margin = margin(18, 18, 22, 18)
      ) +
      stat_smooth(aes(y = token_fixed, group = 1), method = "lm", se = FALSE,
                  color = "red", linetype = "dashed", size = 0.5) +
      stat_smooth(aes(y = -token_not_fixed, group = 1), method = "lm", se = FALSE,
                  color = "blue", linetype = "dashed", size = 0.5)
  }
  
  # Build and combine plots
  plot1 <- plot_group(data[data$type == "exhaustive", ], y_label = TRUE)
  plot2 <- plot_group(data[data$type == "early_stop", ])
  plot3 <- plot_group(data[data$type == "es_accsorted", ], y_label = TRUE)
  plot4 <- plot_group(data[data$type == "es_unisorted", ])
  
  combined_plot <- (plot1 | plot2) / (plot3 | plot4)
  if (legend_enabled) {
    combined_plot <- combined_plot + plot_layout(guides = "collect")
  }
  
  # Save a separate legend when requested.
  if (!legend_enabled && !is.null(legend_output_path)) {
    extract_legend <- function(p) {
      plot_grob <- ggplotGrob(p)
      legend_index <- which(sapply(plot_grob$grobs, function(x) x$name) == "guide-box")
      if (length(legend_index) == 0) {
        return(NULL)
      }
      plot_grob$grobs[[legend_index[1]]]
    }
    legend_plot <- plot_group(data, y_label = FALSE, show_legend = TRUE) +
      theme(
        legend.position = "bottom",
        legend.direction = "horizontal",
        legend.box.margin = margin(5, 5, 5, 5),
        legend.background = element_rect(color = "gray70", fill = "white", linewidth = 0.6),
        plot.margin = margin(5, 5, 5, 5)
      )
    legend_grob <- extract_legend(legend_plot)
    if (!is.null(legend_grob)) {
      legend_width <- convertWidth(sum(legend_grob$widths), "in", valueOnly = TRUE)
      legend_height <- convertHeight(sum(legend_grob$heights), "in", valueOnly = TRUE)
      legend_width <- legend_width + 0.2
      legend_height <- legend_height + 0.2
      ggsave(legend_grob,
             filename = legend_output_path,
             width = max(legend_output_width, legend_width),
             height = max(legend_output_height, legend_height),
             dpi = 600)
    }
  }
  
  # Save
  ggsave(combined_plot,
         filename = output_filename,
         path = output_dir,
         width = 11,
         height = 7,
         dpi = 600)
  
  return(combined_plot)
}

legend_written <- FALSE
legend_output_path <- file.path(base_dir, "rq3_symmetry_bar_setting_token_legend.png")

for (dataset in datasets) {
  for (model in models) {
    f <- plot_inference_token_symmetry(dataset, model, base_dir, file_tag = "token",
                                       input_file_name = "token_summary_symmetry.csv",
                                       font_size = 20, legend_enabled = FALSE,
                                       legend_output_path = if (!legend_written) legend_output_path else NULL)
    legend_written <- TRUE
    print(f)
  }
}






# ===================================RQ3: 4.1 scatter token vs accuracy===================================
# ===================================RQ3: 4.2 scatter time vs accuracy===================================
scatter_plot_accuracy_vs_metric <- function(dataset, model_name, base_dir, input_file_name, x_column, x_label, file_tag, font_size = 12) {
  input_path <- file.path(base_dir, dataset, model_name, input_file_name)
  output_dir <- file.path(base_dir, dataset, model_name)
  output_filename <- paste0("rq3_scatter_accuracy_", file_tag, "_", shorten_name(dataset), "_", shorten_name(model_name), ".png")
  
  df <- read_csv(input_path, show_col_types = FALSE)
  
  # Define setting name mapping
  setting_labels <- c(
    "1" = "Baseline",
    "2" = "CFN-modified",
    "3" = "CFN-all",
    "4" = "FN-modified",
    "5" = "FN-all",
    "6" = "FLN-all",
    "7" = "FN-pair",
    "8" = "FL-diff"
  )
  df$setting <- setting_labels[as.character(df$setting_id)]
  
  plot <- ggplot(df, aes(x = .data[[x_column]], y = percentage_solved)) +
    geom_point(size = 3, color = "black", fill = "white", shape = 21, stroke = 0.8) +
    geom_text_repel(
      aes(label = setting),
      size = font_size * 0.26,
      max.overlaps = Inf,
      force = 5,
      box.padding = 0.6,
      point.padding = 0.3,
      segment.size = 0.3,
      segment.color = "gray30"
    ) +
    scale_x_continuous(labels = comma) +
    scale_y_continuous(labels = percent_format(accuracy = 1), limits = c(0, 1)) +
    labs(
      x = x_label,
      y = "Percentage of Bugs Being Fixed"
    ) +
    theme_bw(base_size = font_size) +
    theme(
      panel.border = element_rect(color = "black", fill = NA, size = 0.8),
      panel.grid.major = element_line(color = "gray90"),
      panel.grid.minor = element_blank(),
      axis.title.y = element_text(size = font_size, margin = margin(r = 10)),
      axis.text.x = element_text(size = font_size - 2),
      axis.text.y = element_text(size = font_size - 2),
      axis.title = element_text(size = font_size),
      plot.margin = margin(10, 10, 10, 10)
    )
  
  ggsave(
    filename = output_filename,
    plot = plot,
    path = output_dir,
    width = 7,
    height = 4.5,
    dpi = 600,
    units = "in"
  )
  
  return(plot)
}

for (dataset in datasets) {
  for (model in models) {
    # Token vs Accuracy
    f <- scatter_plot_accuracy_vs_metric(
      dataset = dataset,
      model_name = model,
      base_dir = base_dir,
      input_file_name = "token_vs_accuracy.csv",
      x_column = "total_total_length",
      x_label = "Total Inference Tokens",
      file_tag = "token",
      font_size = 17
    )
    print(f)
    
    # # Time vs Accuracy
    # f <- scatter_plot_accuracy_vs_metric(
    #   dataset = dataset,
    #   model_name = model,
    #   base_dir = base_dir,
    #   input_file_name = "time_vs_accuracy.csv",
    #   x_column = "total_duration_second",
    #   x_label = "Total Inference Time (Seconds)",
    #   file_tag = "time",
    #   font_size = 17
    # )
    # print(f)
  }
}




# ===================================RQ3: 4.3 scatter time vs token===================================
scatter_plot_token_vs_time <- function(dataset, model_name, base_dir, file_tag, token_file, time_file) {
  # 路径设定
  token_path <- file.path(base_dir, dataset, model_name, token_file)
  time_path <- file.path(base_dir, dataset, model_name, time_file)
  output_dir <- file.path(base_dir, dataset, model_name)
  output_filename <- paste0("rq3_scatter_", file_tag, "_vs_time_", shorten_name(dataset), "_", shorten_name(model_name), ".png")
  
  # 加载 CSV
  token_df <- read_csv(token_path, show_col_types = FALSE)
  time_df <- read_csv(time_path, show_col_types = FALSE)
  
  # Setting label mapping
  setting_labels <- c(
    "1" = "Baseline",
    "2" = "CFN-modified",
    "3" = "CFN-all",
    "4" = "FN-modified",
    "5" = "FN-all",
    "6" = "FLN-all",
    "7" = "FN-pair",
    "8" = "FL-diff"
  )
  
  # 合并
  merged_df <- token_df %>%
    select(setting_id, total_total_length) %>%
    inner_join(time_df %>% select(setting_id, total_duration_second), by = "setting_id") %>%
    mutate(setting = setting_labels[as.character(setting_id)])
  
  # 绘图
  plot <- ggplot(merged_df, aes(x = total_total_length, y = total_duration_second)) +
    geom_point(size = 3, color = "black", fill = "white", shape = 21, stroke = 0.8) +
    geom_text_repel(
      aes(label = setting),
      size = 3.2,
      max.overlaps = Inf,
      force = 5,
      box.padding = 0.6,
      point.padding = 0.3,
      segment.size = 0.3,
      segment.color = "gray30"
    ) +
    scale_x_continuous(labels = comma) +
    scale_y_continuous(labels = comma) +
    labs(
      x = "Total Inference Tokens",
      y = "Total Inference Time (Seconds)"
    ) +
    theme_bw(base_size = 12) +
    theme(
      panel.border = element_rect(color = "black", fill = NA, size = 0.8),
      panel.grid.major = element_line(color = "gray90"),
      panel.grid.minor = element_blank(),
      axis.title.y = element_text(margin = margin(r = 10)),
      axis.text.x = element_text(size = 10),
      axis.text.y = element_text(size = 10),
      axis.title = element_text(size = 11),
      plot.margin = margin(10, 10, 10, 10)
    )
  
  # 保存图像
  ggsave(
    filename = output_filename,
    plot = plot,
    path = output_dir,
    width = 7,
    height = 4.5,
    dpi = 600,
    units = "in"
  )
  
  return(plot)
}

# 示例运行
for (dataset in datasets) {
  for (model in models) {
    p <- scatter_plot_token_vs_time(dataset, model, base_dir, file_tag = "token", token_file = "token_vs_accuracy.csv", time_file = "time_vs_accuracy.csv")
    print(p)
    
    # # token weighted
    # p <- scatter_plot_token_vs_time(dataset, model, base_dir, file_tag = "token_weighted", token_file = "token_vs_accuracy_weighted.csv", time_file = "time_vs_accuracy.csv")
    # print(p)
  }
}



# ===================================Discussion: run baseline 7 times for statistical tests check===================================
# Verify current working directory
setwd(here("analysis"))
getwd()  # Should show: .../fm-apr-replay/analysis
# Config
base_dir <- "RQ1_2"
print(base_dir)
for (dataset in datasets) {
  for (model in models) {
    cat("\n========================", dataset, model, "========================\n")
    input_file_path <- file.path(base_dir, dataset, model, "baseline_pass_at_k_10_7_groups.csv")
    data <- read.csv(input_file_path)
    # Remove the percentage signs and convert to numeric
    data[, -1] <- lapply(data[, -1], function(x) as.numeric(gsub("%", "", x)))
    
    # Calculate mean, standard deviation, and coefficient of variation (CV)
    data$mean <- rowMeans(data[, -1])  # Assuming the first column is 'pass@k'
    data$std_dev <- apply(data[, -1], 1, sd)  # Calculate standard deviation for each row
    data$cv <- (data$std_dev / data$mean) * 100  # CV in percentage
  
    # Print the results
    print(data[, c("k", "mean", "std_dev", "cv")])
  }
}





