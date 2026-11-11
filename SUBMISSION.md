# Submission

Fork URL: <!-- paste the URL of your fork here -->

## Files to commit

- [ ] `findings.json`: what you found in the old image
- [ ] `Dockerfile.fixed` and `.dockerignore`: the rebuilt image

## Questions

Answer in your own words. Where a question asks for output, paste it in a code block.

### Q1. Paste `docker history --no-trunc legacy-pollie:1` (the interesting lines). Which instruction created the layer that contains the token, and which later instruction "deleted" it? Why is the secret still in the image?

**Your answer:**

<!-- replace this line with your answer -->

### Q2. Show how you extracted the layers (`docker save` then `tar`) and found the token inside one of them. Paste the commands and the path of the file. What is an image, physically?

**Your answer:**

<!-- replace this line with your answer -->

### Q3. Which layer is the largest and what created it? List three things in the legacy image that a production container does not need.

**Your answer:**

<!-- replace this line with your answer -->

### Q4. The image runs as root. Prove it from the image config and from a running container. What can a process running as root inside a container do to the host if the container is misconfigured?

**Your answer:**

<!-- replace this line with your answer -->

### Q5. Why did `RUN rm /app/.env` not remove the secret, and which two techniques stop it (a multi-stage build; `RUN --mount=type=secret`)? Which one did you use and why?

**Your answer:**

<!-- replace this line with your answer -->

### Q6. Rotating the token is the first thing you do. Why is cleaning the image the second, and what else could have copied the image already?

**Your answer:**

<!-- replace this line with your answer -->

### Q7. Paste the output of `./verify.sh`. It must end with **ALL CHECKS PASSED**.

**Your answer:**

<!-- replace this line with your answer -->

### Q8. **Tear down.** Paste the output of `./verify-teardown.sh`. It must end with **TEARDOWN VERIFIED**.

**Your answer:**

<!-- replace this line with your answer -->
