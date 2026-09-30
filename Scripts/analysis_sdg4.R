#!/usr/bin/env Rscript
# Reproducible quantitative analysis for the SDG4 AI-access dataset.
# Primary inference: two-sided pooled-variance independent-samples t tests
# (Premium minus Free), as specified in the manuscript (df = n1+n2-2).
# Run: Rscript analysis_sdg4.R [data.csv] [output_directory]

args <- commandArgs(trailingOnly = TRUE)
data_path <- if (length(args) >= 1) args[[1]] else "/mnt/data/SDG4_Quant_Data.csv"
outdir <- if (length(args) >= 2) args[[2]] else "sdg4_analysis_results_R"
outcomes <- c("Lexical_TTR", "Syntactic_Cscore", "Cohesion_Score")
groups <- c("Premium", "Free")
required <- c("Participant_ID", "Group", outcomes)
if (!file.exists(data_path)) stop("Input data file not found: ", data_path)
dir.create(outdir, recursive = TRUE, showWarnings = FALSE)
dat <- read.csv(data_path, stringsAsFactors = FALSE, check.names = FALSE)
missing <- setdiff(required, names(dat))
if (length(missing)) stop("Missing required columns: ", paste(missing, collapse=", "), ". Use 'Group' (not 'Condition').")
if (!nrow(dat)) stop("Input dataset contains no rows.")
if (anyNA(dat$Participant_ID) || anyDuplicated(dat$Participant_ID)) stop("Participant_ID values must be present and unique.")
if (anyNA(dat$Group) || !all(dat$Group %in% groups) || !setequal(unique(dat$Group), groups)) stop("Group must contain both Premium and Free only.")
for (v in outcomes) {
  dat[[v]] <- suppressWarnings(as.numeric(dat[[v]]))
  if (anyNA(dat[[v]]) || any(!is.finite(dat[[v]]))) stop(v, " contains missing, nonnumeric, or non-finite values.")
}
if (any(dat$Lexical_TTR < 0 | dat$Lexical_TTR > 1)) stop("Lexical_TTR must lie between 0 and 1.")
if (any(dat$Cohesion_Score < 0 | dat$Cohesion_Score > 10)) stop("Cohesion_Score must lie between 0 and 10.")
counts <- table(factor(dat$Group, levels=groups))
if (any(counts < 2)) stop("Each group must have at least two observations.")

# Descriptive statistics.
quantile_type7 <- function(x, p) as.numeric(quantile(x, probs=p, type=7, names=FALSE))
desc_rows <- list(); k <- 1
for (v in outcomes) for (g in groups) {
  x <- dat[dat$Group == g, v]
  desc_rows[[k]] <- data.frame(Outcome=v, Group=g, n=length(x), Mean=mean(x), SD=sd(x),
    Median=median(x), Q1=quantile_type7(x,.25), Q3=quantile_type7(x,.75), Minimum=min(x), Maximum=max(x))
  k <- k+1
}
desc <- do.call(rbind, desc_rows)
write.csv(desc, file.path(outdir,"descriptive_statistics.csv"), row.names=FALSE, na="")

# Pooled Student tests (primary), mean-difference CIs, effect sizes, diagnostics, Welch sensitivity.
res_rows <- list()
for (i in seq_along(outcomes)) {
  v <- outcomes[i]; a <- dat[dat$Group=="Premium",v]; b <- dat[dat$Group=="Free",v]
  n1 <- length(a); n2 <- length(b); dfree <- n1+n2-2
  m1 <- mean(a); m2 <- mean(b); s1 <- sd(a); s2 <- sd(b)
  sp <- sqrt(((n1-1)*s1^2+(n2-1)*s2^2)/dfree)
  difference <- m1-m2; se <- sp*sqrt(1/n1+1/n2)
  tt <- t.test(a,b,var.equal=TRUE,alternative="two.sided")
  d <- difference/sp; J <- 1-3/(4*dfree-1); g <- J*d
  # Median-centered Levene/Brown-Forsythe test (base R implementation).
  z <- c(abs(a-median(a)),abs(b-median(b)))
  grp <- factor(c(rep("Premium",n1),rep("Free",n2)))
  lev <- oneway.test(z ~ grp, var.equal=TRUE)
  welch <- t.test(a,b,var.equal=FALSE,alternative="two.sided")
  sh1 <- if (n1 >= 3 && n1 <= 5000) shapiro.test(a)$p.value else NA_real_
  sh2 <- if (n2 >= 3 && n2 <= 5000) shapiro.test(b)$p.value else NA_real_
  res_rows[[i]] <- data.frame(Outcome=v, Premium_n=n1, Free_n=n2, Premium_mean=m1, Premium_SD=s1,
    Free_mean=m2, Free_SD=s2, Mean_difference_Premium_minus_Free=difference,
    Difference_CI95_low=difference-qt(.975,dfree)*se, Difference_CI95_high=difference+qt(.975,dfree)*se,
    Student_t=unname(tt$statistic), Student_df=dfree, Student_p=tt$p.value, Cohens_d=d, Hedges_g=g,
    Levene_median_stat=unname(lev$statistic), Levene_median_p=lev$p.value,
    Shapiro_Premium_p=sh1, Shapiro_Free_p=sh2,
    Welch_t=unname(welch$statistic), Welch_df=unname(welch$parameter), Welch_p=welch$p.value)
}
res <- do.call(rbind,res_rows)
res$Student_p_Holm <- p.adjust(res$Student_p,method="holm")
res$Welch_p_Holm <- p.adjust(res$Welch_p,method="holm")
write.csv(res,file.path(outdir,"group_comparisons.csv"),row.names=FALSE,na="")

# Publication-ready mean plot with separate group mean 95% t confidence intervals.
png(file.path(outdir,"group_means_95ci.png"),width=3300,height=1250,res=300)
oldpar <- par(mfrow=c(1,3),mar=c(5,4.6,3.2,1),oma=c(0,0,2,0),las=1)
cols <- c(Premium="#3569a8",Free="#d17a22")
labels <- c(Lexical_TTR="Lexical diversity (TTR)",Syntactic_Cscore="Syntactic complexity (C-score)",Cohesion_Score="Cohesion score")
for (v in outcomes) {
  means <- sds <- ns <- lows <- highs <- numeric(2)
  for (j in seq_along(groups)) {
    x <- dat[dat$Group==groups[j],v]; means[j] <- mean(x); sds[j] <- sd(x); ns[j] <- length(x)
    margin <- qt(.975,ns[j]-1)*sds[j]/sqrt(ns[j]); lows[j] <- means[j]-margin; highs[j] <- means[j]+margin
  }
  ylim <- range(c(lows,highs)); pad <- diff(ylim)*.12; if (pad==0) pad <- .1
  plot(1:2,means,type="n",xaxt="n",xlim=c(.6,2.4),ylim=ylim+c(-pad,pad),
       xlab="AI-access group",ylab="Mean (95% CI)",main=labels[[v]],bty="l")
  axis(1,at=1:2,labels=groups)
  for(j in 1:2){points(j,means[j],pch=19,cex=1.4,col=cols[j]);arrows(j,lows[j],j,highs[j],angle=90,code=3,length=.08,lwd=1.6,col=cols[j])}
  abline(h=pretty(ylim)[1],col="grey90",lty=3)
}
mtext("Linguistic outcomes by AI-access group",outer=TRUE,cex=1.25,font=2)
par(oldpar); dev.off()

# Text summary, with explicit non-causal interpretation.
con <- file(file.path(outdir,"analysis_report.txt"),open="wt",encoding="UTF-8")
writeLines(c("SDG4 quantitative analysis",strrep("=",29),paste("Input:",data_path),
  paste0("N = ",nrow(dat),"; group sizes: Premium=",counts["Premium"],", Free=",counts["Free"]),
  "Primary analysis: two-sided pooled-variance independent-samples Student t tests; contrast = Premium - Free.",
  "Effect size: pooled Cohen's d; Hedges' g also reported. 95% CI is for raw mean difference.",
  "Holm adjustment is across the three primary tests. Welch tests and diagnostics are sensitivity/checks.","","Descriptives (mean +/- SD)"),con)
for(v in outcomes){p <- desc[desc$Outcome==v,]; a <- p[p$Group=="Premium",]; b <- p[p$Group=="Free",]
  writeLines(sprintf("%s: Premium %.4f +/- %.4f; Free %.4f +/- %.4f",v,a$Mean,a$SD,b$Mean,b$SD),con)}
writeLines(c("","Primary tests and diagnostics"),con)
for(i in seq_len(nrow(res))){r<-res[i,]
  writeLines(sprintf("%s: t(%g)=%.3f, p=%.4g, Holm p=%.4g, d=%.3f, g=%.3f, difference=%.4f, 95%% CI [%.4f, %.4f]; Levene p=%.4g, Shapiro p (Premium/Free)=%.4g/%.4g, Welch t(%.2f)=%.3f, p=%.4g",
    r$Outcome,r$Student_df,r$Student_t,r$Student_p,r$Student_p_Holm,r$Cohens_d,r$Hedges_g,
    r$Mean_difference_Premium_minus_Free,r$Difference_CI95_low,r$Difference_CI95_high,
    r$Levene_median_p,r$Shapiro_Premium_p,r$Shapiro_Free_p,r$Welch_df,r$Welch_t,r$Welch_p),con)}
writeLines(c("","Interpretation caveat: this non-randomized between-group dataset has no baseline or covariate data; findings describe group associations and do not establish causal effects of Premium access.",
  "Diagnostics (Shapiro-Wilk and median-centered Levene) are screening tools, not proof of assumptions."),con)
close(con)
cat("Analysis complete. Files:\n")
for(f in c("descriptive_statistics.csv","group_comparisons.csv","analysis_report.txt","group_means_95ci.png")) cat(file.path(outdir,f),"\n")
cat("\nPrimary results:\n")
print(res[,c("Outcome","Student_t","Student_df","Student_p","Student_p_Holm","Cohens_d","Mean_difference_Premium_minus_Free","Difference_CI95_low","Difference_CI95_high")],row.names=FALSE)
