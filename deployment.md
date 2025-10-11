# Deployment

Since the connector is designed as a Docker microservice, it can be deployed in any cloud, for example, using a cloud-specific utility. Below are examples of scripts that you can use, but you can write your own that are simpler or more complex to suit your needs.

!!! note "Note"
    - Hosting expenses for your connectors deployed in cloud platforms **won't be covered** by PortaOne.
    - There is a local deployment option, at no extra cost, to consider:
        - assuming test purposes or development - local PC/laptop;
        - assuming production but low traffic / load (otherwise, extra server(s) is required to handle the load): [Docker Swarm managed via PortaBilling Portainer Stack][docker-swarm].

**Example for GCP**: [deploy as a Cloud Run][gcp-deploy]. Official guide on how to deploy Cloud Run services you can find [here][gcp-deploy-official-guide].

A Cloud Run service URL typically follows the format: `https://[TAG---]SERVICE_IDENTIFIER.run.app`. `SERVICE_IDENTIFIER` is a unique, stable identifier for the service, and the TAG refers to the traffic tag of the specific revision. The `SERVICE_IDENTIFIER` includes a random string and the region shortcut.

`https://[TAG---]SERVICE_NAME-PROJECT_NUMBER.REGION.run.app`

where:

- **TAG** is the optional [traffic tag][traffic-tag] for the revision that you are requesting.
- **PROJECT_NUMBER** is the Google Cloud [project number][creating-managing-projects].
- **SERVICE_NAME** is the name of the Cloud Run service.
- **REGION** is the name of the region, such as `us-central1`.

**Example for AWS**: [deploy as an App Runner][aws-deploy]. Official guide on how to deploy App Runner services you can find [here][aws-deploy-official-guide].

An App Runner service URL typically follows the format: `https://[service-id].[region].awsapprunner.com` where `service-id` is a unique identifier for your service and `region` is the AWS region where your service is hosted.

For example: `https://abcd1234efgh.us-east-1.awsapprunner.com`

## Infrastructure Considerations

The default deployment of [NSPS][nsps], PortaBilling, and Connector/Core is intended to run in a **public internet environment**, where services can communicate freely over the network. However, in specific cases, it may be necessary to restrict public access to components for security reasons.

At this time, we can provide a **static IP address** used by NSPS to make requests to both the Connector and PortaBilling.

VPN connectivity is not currently supported and is under consideration ([DO-5364][do-5364]).

<!-- References -->
[gcp-deploy]: https://gitlab.portaone.com:8949/read-only/wtl_hlr_hss_connector/-/tree/main/_gcp-deploy?ref_type=heads
[gcp-deploy-official-guide]: https://cloud.google.com/run/docs/deploying#gcloud
[traffic-tag]: https://cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration#tags
[creating-managing-projects]: https://cloud.google.com/resource-manager/docs/creating-managing-projects
[aws-deploy]: https://gitlab.portaone.com:8949/read-only/wtl_hlr_hss_connector/-/tree/main/_aws-deploy?ref_type=heads
[aws-deploy-official-guide]: https://docs.aws.amazon.com/apprunner/latest/dg/manage-deploy.html
[do-5364]: https://youtrack.portaone.com/issue/DO-5364

[nsps]: NSPS/nsps-overview.md