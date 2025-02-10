import yaml


def main():
    with open("../../values.yaml", "r") as valuesfile:
        values = yaml.safe_load(valuesfile)
        version = values["metricsexporterVersion"]
        print(f"version={version}")


if __name__ == "__main__":
    main()
