#!/bin/bash

echo "========== ECS Services =========="
aws ecs describe-services \
  --cluster expense-cluster \
  --services expense-app-svc expense-frontend-svc \
  --region ap-south-1 \
  --query "services[*].{Name:serviceName,Running:runningCount,Desired:desiredCount,Status:status}" \
  --output table

echo ""
echo "========== Backend Target Health =========="
aws elbv2 describe-target-health \
  --target-group-arn "arn:aws:elasticloadbalancing:ap-south-1:071750954511:targetgroup/expense-backend-tg/29cbaed9103b440b" \
  --region ap-south-1 \
  --query "TargetHealthDescriptions[*].{State:TargetHealth.State,Reason:TargetHealth.Reason}" \
  --output table

echo ""
echo "========== Frontend Target Health =========="
aws elbv2 describe-target-health \
  --target-group-arn "arn:aws:elasticloadbalancing:ap-south-1:071750954511:targetgroup/expense-frontend-tg/c11b8541000ea8b8" \
  --region ap-south-1 \
  --query "TargetHealthDescriptions[*].{State:TargetHealth.State,Reason:TargetHealth.Reason}" \
  --output table

echo ""
echo "========== Endpoint Tests =========="
printf "Frontend:    "
curl -sI https://pocketly.sachinsinghchaudhary.com.np/ --max-time 10 | head -1

printf "API schema:  "
curl -sI https://pocketly.sachinsinghchaudhary.com.np/api/schema/ --max-time 10 | head -1

printf "API root:    "
curl -sI https://pocketly.sachinsinghchaudhary.com.np/api/ --max-time 10 | head -1

echo ""
echo "========== Signup Test =========="
curl -s -X POST https://pocketly.sachinsinghchaudhary.com.np/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"healthcheck_$(date +%s)\",\"email\":\"health_$(date +%s)@test.com\",\"password\":\"TestPass123!@#\"}" \
  --max-time 15 \
  | python3 -m json.tool 2>/dev/null || echo "(signup endpoint may differ - check your urls.py)"

echo ""
echo "========== Recent Errors (last 5 min) =========="
aws logs tail /ecs/expense-app --since 5m --region ap-south-1 2>&1 \
  | grep -iE "error|traceback|exception|500" | grep -v drf_spectacular | head -10 || echo "(no errors)"
