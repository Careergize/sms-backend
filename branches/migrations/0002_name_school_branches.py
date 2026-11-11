from django.db import migrations, models

BRANCH_NAMES = (
    ("Central", "Vanchiyoor"),
    ("North", "Peroorkada"),
    ("East", "Kulathoor"),
    ("South", "Manakkadu"),
    ("West", "Njakkal"),
)


def update_demo_branches(apps, schema_editor):
    branches = apps.get_model("branches", "Branch").objects.using(schema_editor.connection.alias)
    for index, (area, name) in enumerate(BRANCH_NAMES, start=1):
        branches.filter(code=f"B{index:02}", name=f"Branch {index}", area=area).update(name=name, area="")
    branches.filter(code="B06", name="Branch 6", area="Airport").update(is_active=False)


def restore_demo_branches(apps, schema_editor):
    branches = apps.get_model("branches", "Branch").objects.using(schema_editor.connection.alias)
    for index, (area, name) in enumerate(BRANCH_NAMES, start=1):
        branches.filter(code=f"B{index:02}", name=name, area="").update(name=f"Branch {index}", area=area)
    branches.filter(code="B06", name="Branch 6", area="Airport").update(is_active=True)


class Migration(migrations.Migration):
    dependencies = [("branches", "0001_initial")]

    operations = [
        migrations.AddField(model_name="branch", name="is_active", field=models.BooleanField(default=True)),
        migrations.AlterField(model_name="branch", name="area", field=models.CharField(blank=True, max_length=100)),
        migrations.RunPython(update_demo_branches, restore_demo_branches),
    ]
