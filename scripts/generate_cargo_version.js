const fs = require('fs');
const execSync = require('child_process').execSync;
const NAME_REGEX = /name = "(?<name>.*)"/;
const versionRegexFactory = (packageName) =>
  new RegExp(`${packageName} = "(?<version>.*)".*`);

const { MAJOR_VERSION: majorStr, MINOR_VERSION: minorStr } = process.env;
const cargoTomlFilepath = `${process.env.CARGO_TOML_DIRPATH || '.'}/Cargo.toml`;
const cargoTomlFile = fs.readFileSync(cargoTomlFilepath, 'utf-8');
const packageNameLine = cargoTomlFile.split('\n')[1];
const packageName = NAME_REGEX.exec(packageNameLine).groups?.name;

console.log('Invoked with:', {
  cargoTomlFilepath,
  packageName,
  majorStr,
  minorStr
});

if (!packageName || !majorStr || !minorStr) {
  console.error(
    'Missing environment values. Required values are: MAJOR_VERSION and MINOR_VERSION.'
  );
  process.exit(1);
}

const major = parseInt(majorStr);
const minor = parseInt(minorStr);

const searchOutput = execSync(`cargo search ${packageName} --limit 1`, {
  encoding: 'utf-8'
});
const packageData = searchOutput.split('\n', 1)[0];
const VERSION_REGEX = versionRegexFactory(packageName);
const match = VERSION_REGEX.exec(packageData);
const lastVersionString = match?.groups?.version;

if (!lastVersionString) {
  console.warn('Package not found in crates.io');
  console.warn('Publishing with version 0.1.0...');
  execSync(`echo "0.1.0" > version.out`);
  process.exit(0);
}

const [lastMajor, lastMinor, lastPatch] = lastVersionString
  .split('.')
  .map((val) => parseInt(val));

if (major < lastMajor || (major === lastMajor && minor < lastMinor)) {
  console.error(
    `Invalid major/minor requested. Last version published is: ${lastVersion}`
  );
  process.exit(3);
}

if (major > lastMajor + 1) {
  console.warn(`Trying to advance major from ${lastMajor} to ${major}`);
  process.exit(4);
}

if (major === lastMajor && minor > lastMinor + 1) {
  console.warn(`Trying to advance minor from ${lastMinor} to ${major}`);
  process.exit(4);
}

let version;

if (major > lastMajor) {
  console.info(`Advancing major from ${lastMajor} to ${major}`);
  console.info(`Starting major with minor: ${minor}`);
  version = `${major}.${minor}.0`;
} else if (minor > lastMinor) {
  console.info(`Advancing minor from ${lastMinor} to ${minor}`);
  version = `${lastMajor}.${minor}.0`;
} else {
  version = `${lastMajor}.${lastMinor}.${lastPatch + 1}`;
}

console.info('Generated version:', version);
execSync(`echo "${version}" > version.out`);
